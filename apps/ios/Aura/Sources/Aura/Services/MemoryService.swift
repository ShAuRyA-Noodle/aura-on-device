// MemoryService.swift
// Local SQLite-backed memory graph using GRDB.swift. Mirrors the schema in
// `aura/memory/schema.sql` (technical_spec.md §6.2). Provides:
//   * Insert / fetch nodes, edges, traces.
//   * Append-only audit log with running SHA-256 hash chain.
//   * Time-range delete.
//   * Export the entire graph as JSON to a file the Files app can read.
//
// The DB lives at `Application Support/Aura/aura.sqlite`. Encryption-at-rest
// is provided by iOS Data Protection (`.completeFileProtection`); the
// production build will swap in SQLCipher when the team finishes vetting it.
import Foundation
#if canImport(CryptoKit)
import CryptoKit
#endif
#if canImport(GRDB)
import GRDB
#endif

@available(iOS 17.0, macOS 14.0, *)
public actor MemoryService {
	public static let shared = MemoryService()

	public enum MemoryServiceError: Error, LocalizedError {
		case notConfigured
		case ioFailed(Error)
		case unsupportedRange

		public var errorDescription: String? {
			switch self {
			case .notConfigured:    return "Memory store has not been opened."
			case .ioFailed(let e):  return "Memory I/O failed: \(e.localizedDescription)"
			case .unsupportedRange: return "Delete range is invalid (start must be before end)."
			}
		}
	}

	public struct NodeRow: Codable, Equatable, Identifiable, Sendable {
		public let id: String
		public let type: String
		public let dataJSON: String
		public let ts: Int64
		public let retentionClass: String

		enum CodingKeys: String, CodingKey {
			case id
			case type
			case dataJSON = "data_json"
			case ts
			case retentionClass = "retention_class"
		}
	}

	public struct AuditEntry: Codable, Equatable, Identifiable, Sendable {
		public let seq: Int64
		public let ts: Int64
		public let op: String
		public let targetType: String?
		public let targetId: String?
		public let agent: String?
		public let payloadJSON: String?
		public let hashChain: String

		public var id: Int64 { seq }
	}

	#if canImport(GRDB)
	private var pool: DatabasePool?
	#endif

	private init() {}

	// MARK: - Lifecycle

	public func open() async throws {
		#if canImport(GRDB)
		guard pool == nil else { return }
		do {
			let dir = try MemoryService.databaseDirectory()
			try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
			let url = dir.appendingPathComponent("aura.sqlite")
			var config = Configuration()
			config.prepareDatabase { db in
				try db.execute(sql: "PRAGMA foreign_keys = ON")
			}
			let pool = try DatabasePool(path: url.path, configuration: config)
			try MemoryService.applySchema(pool: pool)
			self.pool = pool
		} catch {
			throw MemoryServiceError.ioFailed(error)
		}
		#endif
	}

	public func close() async {
		#if canImport(GRDB)
		pool = nil
		#endif
	}

	private static func databaseDirectory() throws -> URL {
		let support = try FileManager.default.url(
			for: .applicationSupportDirectory,
			in: .userDomainMask,
			appropriateFor: nil,
			create: true
		)
		return support.appendingPathComponent("Aura", isDirectory: true)
	}

	#if canImport(GRDB)
	private static func applySchema(pool: DatabasePool) throws {
		try pool.write { db in
			try db.execute(sql: """
				CREATE TABLE IF NOT EXISTS nodes (
					id              TEXT PRIMARY KEY,
					type            TEXT NOT NULL,
					data_json       TEXT NOT NULL,
					ts              INTEGER NOT NULL,
					retention_class TEXT NOT NULL DEFAULT 'default'
				);
				CREATE INDEX IF NOT EXISTS idx_nodes_type_ts ON nodes(type, ts DESC);
				CREATE INDEX IF NOT EXISTS idx_nodes_ts ON nodes(ts DESC);

				CREATE TABLE IF NOT EXISTS edges (
					id     TEXT PRIMARY KEY,
					src    TEXT NOT NULL,
					dst    TEXT NOT NULL,
					type   TEXT NOT NULL,
					weight REAL DEFAULT 1.0,
					ts     INTEGER NOT NULL
				);
				CREATE INDEX IF NOT EXISTS idx_edges_src_type ON edges(src, type);
				CREATE INDEX IF NOT EXISTS idx_edges_dst_type ON edges(dst, type);

				CREATE TABLE IF NOT EXISTS traces (
					trace_id     TEXT PRIMARY KEY,
					ts           INTEGER NOT NULL,
					payload_json TEXT NOT NULL,
					outcome      TEXT NOT NULL
				);
				CREATE INDEX IF NOT EXISTS idx_traces_ts ON traces(ts DESC);

				CREATE TABLE IF NOT EXISTS audit_log (
					seq         INTEGER PRIMARY KEY AUTOINCREMENT,
					ts          INTEGER NOT NULL,
					op          TEXT NOT NULL,
					target_type TEXT,
					target_id   TEXT,
					agent       TEXT,
					payload_json TEXT,
					hash_chain  TEXT NOT NULL
				);
				CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_log(ts);

				CREATE TABLE IF NOT EXISTS settings (
					key        TEXT PRIMARY KEY,
					value_json TEXT NOT NULL,
					updated_ts INTEGER NOT NULL
				);
				""")
		}
	}
	#endif

	// MARK: - Writes

	public func insertNode(id: String, type: String, dataJSON: String, retentionClass: String = "default") async throws {
		#if canImport(GRDB)
		guard let pool else { throw MemoryServiceError.notConfigured }
		let ts = Int64(Date().timeIntervalSince1970)
		do {
			try pool.write { db in
				try db.execute(
					sql: "INSERT OR REPLACE INTO nodes(id, type, data_json, ts, retention_class) VALUES (?, ?, ?, ?, ?)",
					arguments: [id, type, dataJSON, ts, retentionClass]
				)
			}
			try await appendAudit(op: "write", targetType: type, targetId: id, payloadJSON: dataJSON, agent: nil)
		} catch let error as MemoryServiceError {
			throw error
		} catch {
			throw MemoryServiceError.ioFailed(error)
		}
		#endif
	}

	public func insertTrace(_ trace: Trace) async throws {
		#if canImport(GRDB)
		guard let pool else { throw MemoryServiceError.notConfigured }
		let ts = Int64(Date().timeIntervalSince1970)
		guard let payload = trace.prettyJSON else { return }
		let outcome = trace.outcome.rawValue
		do {
			try pool.write { db in
				try db.execute(
					sql: "INSERT OR REPLACE INTO traces(trace_id, ts, payload_json, outcome) VALUES (?, ?, ?, ?)",
					arguments: [trace.traceId, ts, payload, outcome]
				)
			}
			try await appendAudit(op: "write", targetType: "Trace", targetId: trace.traceId, payloadJSON: nil, agent: "orchestrator")
		} catch let error as MemoryServiceError {
			throw error
		} catch {
			throw MemoryServiceError.ioFailed(error)
		}
		#endif
	}

	// MARK: - Reads

	public func nodeCount() async throws -> Int {
		#if canImport(GRDB)
		guard let pool else { throw MemoryServiceError.notConfigured }
		return try pool.read { db in
			try Int.fetchOne(db, sql: "SELECT COUNT(*) FROM nodes") ?? 0
		}
		#else
		return 0
		#endif
	}

	public func edgeCount() async throws -> Int {
		#if canImport(GRDB)
		guard let pool else { throw MemoryServiceError.notConfigured }
		return try pool.read { db in
			try Int.fetchOne(db, sql: "SELECT COUNT(*) FROM edges") ?? 0
		}
		#else
		return 0
		#endif
	}

	public func lastWrite() async throws -> Date? {
		#if canImport(GRDB)
		guard let pool else { throw MemoryServiceError.notConfigured }
		let ts: Int64? = try pool.read { db in
			try Int64.fetchOne(db, sql: "SELECT MAX(ts) FROM nodes")
		}
		guard let ts else { return nil }
		return Date(timeIntervalSince1970: TimeInterval(ts))
		#else
		return nil
		#endif
	}

	public func auditEntries(limit: Int = 200) async throws -> [AuditEntry] {
		#if canImport(GRDB)
		guard let pool else { throw MemoryServiceError.notConfigured }
		return try pool.read { db in
			try AuditEntry.fetchAll(
				db,
				sql: "SELECT seq, ts, op, target_type, target_id, agent, payload_json, hash_chain FROM audit_log ORDER BY seq DESC LIMIT ?",
				arguments: [limit]
			)
		}
		#else
		return []
		#endif
	}

	// MARK: - Delete

	@discardableResult
	public func deleteRange(start: Date, end: Date) async throws -> Int {
		#if canImport(GRDB)
		guard let pool else { throw MemoryServiceError.notConfigured }
		guard start < end else { throw MemoryServiceError.unsupportedRange }
		let s = Int64(start.timeIntervalSince1970)
		let e = Int64(end.timeIntervalSince1970)
		let removed: Int = try pool.write { db in
			try db.execute(
				sql: "DELETE FROM nodes WHERE ts >= ? AND ts < ?",
				arguments: [s, e]
			)
			try db.execute(
				sql: "DELETE FROM traces WHERE ts >= ? AND ts < ?",
				arguments: [s, e]
			)
			return db.changesCount
		}
		try await appendAudit(
			op: "delete_range",
			targetType: nil,
			targetId: nil,
			payloadJSON: "{\"start\":\(s),\"end\":\(e)}",
			agent: "user"
		)
		return removed
		#else
		return 0
		#endif
	}

	// MARK: - Export

	/// Export the whole graph as a JSON file. Returns the file URL the
	/// caller can hand to a `UIDocumentPickerViewController` or share sheet.
	public func exportJSON() async throws -> URL {
		#if canImport(GRDB)
		guard let pool else { throw MemoryServiceError.notConfigured }
		let dump: [String: Any] = try pool.read { db in
			let nodes = try Row.fetchAll(db, sql: "SELECT id, type, data_json, ts, retention_class FROM nodes")
				.map { row -> [String: Any] in
					[
						"id": row["id"] as? String ?? "",
						"type": row["type"] as? String ?? "",
						"data_json": row["data_json"] as? String ?? "",
						"ts": row["ts"] as? Int64 ?? 0,
						"retention_class": row["retention_class"] as? String ?? "default"
					]
				}
			let edges = try Row.fetchAll(db, sql: "SELECT id, src, dst, type, weight, ts FROM edges")
				.map { row -> [String: Any] in
					[
						"id": row["id"] as? String ?? "",
						"src": row["src"] as? String ?? "",
						"dst": row["dst"] as? String ?? "",
						"type": row["type"] as? String ?? "",
						"weight": row["weight"] as? Double ?? 1.0,
						"ts": row["ts"] as? Int64 ?? 0
					]
				}
			let traces = try Row.fetchAll(db, sql: "SELECT trace_id, ts, payload_json, outcome FROM traces")
				.map { row -> [String: Any] in
					[
						"trace_id": row["trace_id"] as? String ?? "",
						"ts": row["ts"] as? Int64 ?? 0,
						"payload_json": row["payload_json"] as? String ?? "",
						"outcome": row["outcome"] as? String ?? ""
					]
				}
			return [
				"version": 1,
				"exported_at": Int64(Date().timeIntervalSince1970),
				"nodes": nodes,
				"edges": edges,
				"traces": traces
			]
		}
		let data = try JSONSerialization.data(withJSONObject: dump, options: [.prettyPrinted, .sortedKeys])
		let dir = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first
			?? FileManager.default.temporaryDirectory
		let timestamp = ISO8601DateFormatter().string(from: Date())
			.replacingOccurrences(of: ":", with: "-")
		let url = dir.appendingPathComponent("aura-memory-\(timestamp).json")
		do {
			try data.write(to: url, options: [.atomic, .completeFileProtection])
		} catch {
			throw MemoryServiceError.ioFailed(error)
		}
		try await appendAudit(op: "export", targetType: nil, targetId: nil, payloadJSON: nil, agent: "user")
		return url
		#else
		throw MemoryServiceError.notConfigured
		#endif
	}

	// MARK: - Audit chain

	private func appendAudit(op: String, targetType: String?, targetId: String?, payloadJSON: String?, agent: String?) async throws {
		#if canImport(GRDB)
		guard let pool else { throw MemoryServiceError.notConfigured }
		let ts = Int64(Date().timeIntervalSince1970)
		try pool.write { db in
			let prevHash: String = try String.fetchOne(
				db,
				sql: "SELECT hash_chain FROM audit_log ORDER BY seq DESC LIMIT 1"
			) ?? ""
			let raw = "\(prevHash)|\(ts)|\(op)|\(targetType ?? "")|\(targetId ?? "")|\(agent ?? "")|\(payloadJSON ?? "")"
			let hash = MemoryService.sha256(raw)
			try db.execute(
				sql: "INSERT INTO audit_log(ts, op, target_type, target_id, agent, payload_json, hash_chain) VALUES (?, ?, ?, ?, ?, ?, ?)",
				arguments: [ts, op, targetType, targetId, agent, payloadJSON, hash]
			)
		}
		#endif
	}

	private static func sha256(_ string: String) -> String {
		#if canImport(CryptoKit)
		let data = Data(string.utf8)
		let digest = SHA256.hash(data: data)
		return digest.map { String(format: "%02x", $0) }.joined()
		#else
		return String(string.hashValue)
		#endif
	}
}
