"""Builder for the comms synthetic dataset (500 examples).

Deterministic generator: same seed produces the same file. Run with::

    python -m datasets.comms.build_synthetic

Coverage axes:
- Surface: whatsapp (45%), gmail (20%), slack (20%), instagram (15%)
- Label: ACTIONABLE / SOCIAL / BROADCAST / SPAM (roughly balanced, ACTIONABLE
  gets a slight edge so the classifier has enough positive examples).
- Sender names are drawn from a fixed roster of seven (Anu, Manish, Riya,
  Kabir, Mira, Aanya, Rohan) for friend / project mate contexts. Other
  contexts (prof, placement, irctc, mess warden, BMTC, recruiter) use the
  appropriate institutional sender so the role signal stays clean.
- Indian college life: Thapar, hostel mess, DBMS / DSA quizzes, Patiala-Delhi
  IRCTC, BMTC bus delays in Bangalore, prof emails, club coordinators.

The dataset is intentionally noisy and casual — that's what production input
looks like — so the downstream classifier has to do real work.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import List, Tuple

NAMES = ["Anu", "Manish", "Riya", "Kabir", "Mira", "Aanya", "Rohan"]
PROJECT_GROUPS = [
    "group:Thapar-DSA-Project",
    "group:Hostel-G-Floor-3",
    "group:DBMS-Quiz-Squad",
    "group:Aura-Hackathon-Team",
    "group:Capstone-Phase2",
    "group:Patiala-Foodies",
]
PROF_SENDERS = [
    "prof.gupta@thapar.edu",
    "prof.rao@thapar.edu",
    "ta.dbms@thapar.edu",
    "placement@thapar.edu",
    "registrar@thapar.edu",
    "warden.hostelg@thapar.edu",
]
PROMO_SENDERS = [
    "promo@myntra.com",
    "deals@amazon.in",
    "offers@flipkart.com",
    "newsletter@ajio.com",
    "marketing@swiggy.in",
    "promo@bookmyshow.com",
    "BX-PROMO",
    "TM-OFFER",
    "AD-DAILYDEALS",
]
SPAM_NUMBERS = [
    "+91-9999987654",
    "+91-9876543210",
    "+91-9988776655",
    "+91-9123456789",
    "+91-9090909090",
    "+91-7777777777",
    "+91-8888881111",
]


# ---------------------------------------------------------------------------
# Templates by label
# ---------------------------------------------------------------------------

ACTIONABLE_TEMPLATES: List[Tuple[str, str]] = [
    # whatsapp project group / friends
    ("whatsapp | {grp} | {n}: bro can you push the merge before 9? quiz starts then", "whatsapp"),
    ("whatsapp | {grp} | {n}: @you please review the schema diagram before we submit", "whatsapp"),
    ("whatsapp | {grp} | {n}: deadline is tonight, can you confirm your slide is ready", "whatsapp"),
    ("whatsapp | {n} | yaar Zomato order tracking? i paid your share already, send screenshot", "whatsapp"),
    ("whatsapp | {n} | need the github link by 8pm or i submit without you", "whatsapp"),
    ("whatsapp | {n} | aaj DBMS quiz ka scope confirm karega? chapters 6,7 ya bhi 8", "whatsapp"),
    ("whatsapp | {grp} | mess fees due tomorrow morning before 10, pay or no breakfast", "whatsapp"),
    ("whatsapp | {n} | tu aa rahi hai dance practice? 6:30 LT-3 confirm jaldi", "whatsapp"),
    ("whatsapp | {n} | bhai BMTC strike chal raha hai, alternate plan bata", "whatsapp"),
    ("whatsapp | {n} | hostel ka lock toot gaya, warden ko message karna padega aaj", "whatsapp"),
    ("whatsapp | {grp} | {n}: PR is failing CI, can someone push the lint fix urgent", "whatsapp"),
    ("whatsapp | {n} | exam form ka last date kal hai, bhar diya kya?", "whatsapp"),
    ("whatsapp | {n} | tera laptop charger lekar gayi thi, aaj wapas chahiye", "whatsapp"),
    ("whatsapp | {grp} | {n}: prof said submit assignment 3 by 11:59, who's compiling final pdf", "whatsapp"),
    ("whatsapp | {n} | UPI nahi ho raha tera, retry kar ya cash de", "whatsapp"),
    ("whatsapp | {n} | reminder: capstone review at 2pm sharp, dress decent", "whatsapp"),
    ("whatsapp | {n} | report ka format wrong tha, bhejti hu correct one, replace karna", "whatsapp"),
    ("whatsapp | {n} | bhai, please confirm hackathon team list before midnight", "whatsapp"),
    ("whatsapp | {n} | meri report copy karke nikalna ho to bata, last call", "whatsapp"),
    ("whatsapp | {grp} | {n}: deploy slot tonight 11pm, who's monitoring logs", "whatsapp"),
    # gmail prof / placement / irctc
    ("gmail | prof.gupta@thapar.edu | Submit assignment 3 by 11:59 PM tonight. Late = zero.", "gmail"),
    ("gmail | placement@thapar.edu | Pre-placement talk slot: confirm RSVP by today 5pm", "gmail"),
    ("gmail | noreply@irctc.co.in | PNR 8472913 chart prepared. Train 12952 departs 06:15", "gmail"),
    ("gmail | prof.rao@thapar.edu | Quiz reschedule notice: please confirm your availability tomorrow 10am", "gmail"),
    ("gmail | ta.dbms@thapar.edu | Lab assignment 4 grading ready, pick up your sheet by Friday", "gmail"),
    ("gmail | registrar@thapar.edu | Action required: verify your fee receipt within 48 hours", "gmail"),
    ("gmail | warden.hostelg@thapar.edu | Mandatory hostel meeting 7pm today, attendance compulsory", "gmail"),
    ("gmail | placement@thapar.edu | Test slot moved to Saturday 9am, confirm acknowledgement", "gmail"),
    ("gmail | prof.gupta@thapar.edu | Capstone interim report due tomorrow noon, no extensions", "gmail"),
    ("gmail | ta.dbms@thapar.edu | Please share your project github link by EOD", "gmail"),
    # slack
    ("slack | #frontend-team | {n}: PR #482 needs your sign-off before EOD", "slack"),
    ("slack | {n} (DM) | standup moved to 11am. confirm?", "slack"),
    ("slack | #backend | build is red on main, who broke it pls fix before demo at 4", "slack"),
    ("slack | #aura-dev | {n}: @you can you review the merge before standup tomorrow, urgent please", "slack"),
    ("slack | #release | hotfix branch ready, need approval to deploy to prod", "slack"),
    ("slack | {n} (DM) | check the doc i pinged, deadline EOD", "slack"),
    ("slack | #qa | bug found in checkout flow, pls triage before morning", "slack"),
    ("slack | #design | review needed on the new spend mirror screen, due tomorrow 10am", "slack"),
    ("slack | #ops | cert expiring tonight, rotate before midnight", "slack"),
    ("slack | {n} (DM) | sent you the figma, give thumbs up please", "slack"),
    # instagram (real actionable DMs)
    ("instagram | {handle} | yo can u review my pull request? linked in DM. due tonight", "instagram"),
    ("instagram | {handle} | accept my collab invite? deadline is 9pm sharp", "instagram"),
    ("instagram | {handle} | sent you the deck, eod feedback please", "instagram"),
    ("instagram | {handle} | submit the form before midnight or no team entry", "instagram"),
]

SOCIAL_TEMPLATES: List[Tuple[str, str]] = [
    ("whatsapp | {n} | mess ka food kal kaisa tha? kab gayi thi", "whatsapp"),
    ("whatsapp | {n} | aaj match dekha? kohli ne kya banaya yaar", "whatsapp"),
    ("whatsapp | {n} | kal raat ka voice note suna mera? hahaha", "whatsapp"),
    ("whatsapp | {n} | I'm reading the same book as u, finished chapter 4", "whatsapp"),
    ("whatsapp | {n} | new airpods aagaya finally, sound is mad", "whatsapp"),
    ("whatsapp | {n} | mera filter hatake meme bhej raha hai? ruk", "whatsapp"),
    ("whatsapp | {n} | random thought: what if we shifted hostels next sem", "whatsapp"),
    ("whatsapp | {n} | yo that song you sent on insta is lit", "whatsapp"),
    ("whatsapp | {n} | mess ne aaj rajma chawal banaya, finally", "whatsapp"),
    ("whatsapp | {n} | you saw the new Vivek Bumrah post? legit funny", "whatsapp"),
    ("whatsapp | {n} | tu kab last gym gaya tha? haha", "whatsapp"),
    ("whatsapp | {n} | kya tu single hai still", "whatsapp"),
    ("whatsapp | {n} | exam ke baad goa plan?", "whatsapp"),
    ("whatsapp | {n} | mera dog new trick seekha, video bhejti hu", "whatsapp"),
    ("whatsapp | {n} | feeling so unmotivated yaar", "whatsapp"),
    ("whatsapp | {n} | mom called, gave full lecture about hostel food", "whatsapp"),
    ("whatsapp | {n} | ye GPT 5 cheez sahi hai ya hype", "whatsapp"),
    ("whatsapp | {n} | i think i'm growing out of this hostel vibe", "whatsapp"),
    ("whatsapp | {n} | saala laptop again hanging", "whatsapp"),
    ("whatsapp | {n} | book recommendation chaiye, fiction", "whatsapp"),
    ("whatsapp | {n} | kal raat ka chai session legendary tha", "whatsapp"),
    ("whatsapp | {n} | lol that meme tho", "whatsapp"),
    ("whatsapp | {n} | haha same fr", "whatsapp"),
    ("whatsapp | {n} | ngl that one was bad", "whatsapp"),
    ("whatsapp | {n} | bruh, mess wifi is back", "whatsapp"),
    ("whatsapp | {n} | tbh i kinda miss home", "whatsapp"),
    ("whatsapp | {n} | sleeping at 3 again, pray for me", "whatsapp"),
    ("whatsapp | {n} | autocorrect ne phir se pakad liya", "whatsapp"),
    ("whatsapp | {n} | gn yaar, kal milte", "whatsapp"),
    ("whatsapp | {n} | wait you saw rohan's reel?", "whatsapp"),
    ("instagram | {handle} | posted a reel, lemme know what u think", "instagram"),
    ("instagram | {handle} | hostel sky pics, no filter", "instagram"),
    ("instagram | {handle} | new portfolio site is live, browse if free", "instagram"),
    ("instagram | {handle} | random fact: i can't whistle", "instagram"),
    ("instagram | {handle} | new dp choice 1 ya choice 2", "instagram"),
    ("instagram | {handle} | mess sandwich was actually decent today", "instagram"),
    ("instagram | {handle} | story dekha mera, u liked?", "instagram"),
    ("instagram | {handle} | swipe up tagging u", "instagram"),
    ("instagram | {handle} | aaj sky was unreal, posted", "instagram"),
    ("slack | {n} (DM) | saw the meme channel, dying", "slack"),
    ("slack | #random | anyone going to the food court at 2", "slack"),
    ("slack | #movies | RRR rewatch tonight, who's in (not now, just polling)", "slack"),
    ("slack | #random | mess maggi vs nilgiris maggi, weigh in", "slack"),
    ("slack | #random | my plant died lol", "slack"),
    ("slack | #random | bake-off entries due, who's submitting cookies", "slack"),
    ("slack | #random | who has spotify family invite link", "slack"),
    ("slack | #random | vending machine ne paise kha liye again", "slack"),
    ("slack | #random | sambhar in mess today legitimately good", "slack"),
    ("slack | #random | weekend plans? someone propose something", "slack"),
]

BROADCAST_TEMPLATES: List[Tuple[str, str]] = [
    ("whatsapp | group:Thapar-CSE-Batch | ANNOUNCEMENT: classes suspended tomorrow due to convocation", "whatsapp"),
    ("whatsapp | group:Hostel-G-Floor-3 | NOTICE: water supply off 8am-10am tomorrow", "whatsapp"),
    ("whatsapp | group:Mess-Updates | Mess closed for cleaning Sunday lunch, dinner usual", "whatsapp"),
    ("whatsapp | group:Aura-Hackathon-Team | Reminder for all: pitch slot at 3pm Saturday", "whatsapp"),
    ("whatsapp | group:Patiala-Foodies | New tea stall open near gate 2, rates same", "whatsapp"),
    ("whatsapp | group:DBMS-Quiz-Squad | Quiz timing changed to 11am, all please note", "whatsapp"),
    ("whatsapp | group:Capstone-Phase2 | Reminder: midpoint review next Wednesday everyone", "whatsapp"),
    ("whatsapp | group:Thapar-CSE-Batch | Library will be open till midnight during exam week", "whatsapp"),
    ("whatsapp | group:Hostel-G-Floor-3 | Pest control on Friday 2-4pm, please vacate rooms", "whatsapp"),
    ("whatsapp | group:Patiala-Foodies | New dosa place 50% off this week only, pin this", "whatsapp"),
    ("whatsapp | group:Mess-Updates | Diwali special menu Saturday dinner everyone welcome", "whatsapp"),
    ("whatsapp | group:Thapar-Sports | Sports day on the 18th, register your event", "whatsapp"),
    ("whatsapp | group:Coding-Club | Workshop on git internals Saturday 4pm LT-2", "whatsapp"),
    ("whatsapp | group:Thapar-Music-Club | Open mic night this Friday, walk-ins welcome", "whatsapp"),
    ("whatsapp | group:Yoga-Club | Morning class moved to 7am, bring your mats", "whatsapp"),
    ("gmail | placement@thapar.edu | Notice: TCS NQT registrations open till May 15", "gmail"),
    ("gmail | placement@thapar.edu | Announcement: Wipro PPT Wednesday 4pm Auditorium", "gmail"),
    ("gmail | registrar@thapar.edu | Holiday notice: campus closed Monday on account of Buddha Purnima", "gmail"),
    ("gmail | warden.hostelg@thapar.edu | Attention all: hostel inspection on Saturday 11am", "gmail"),
    ("gmail | dean.academics@thapar.edu | Reminder for all faculty and students: convocation rehearsal Friday", "gmail"),
    ("gmail | library@thapar.edu | Book return drive next week, check your accounts", "gmail"),
    ("gmail | sports@thapar.edu | Annual sports meet schedule attached for everyone", "gmail"),
    ("gmail | aluminet@thapar.edu | Alumni meet announcement: registrations open this week", "gmail"),
    ("gmail | clubs@thapar.edu | Coding club hackathon next month, save the date", "gmail"),
    ("gmail | mess-committee@thapar.edu | Mess menu revision feedback form, all students", "gmail"),
    ("slack | #announcements | All hands meeting Friday 4pm, calendar invite incoming", "slack"),
    ("slack | #announcements | Code freeze starts Monday for the demo build", "slack"),
    ("slack | #all-students | Reminder for all: registrations close tonight midnight", "slack"),
    ("slack | #all-hostels | Notice: hostel curfew 11pm this weekend due to event", "slack"),
    ("slack | #all-cse | Annual fest sponsorship pitch competition next Tuesday", "slack"),
    ("instagram | thapar.official | Annual cultural fest dates announced, check stories", "instagram"),
    ("instagram | thapar.placements | Notice: career fair next Monday auditorium", "instagram"),
    ("instagram | thapar.coding.club | Hackathon registrations live for all, link in bio", "instagram"),
    ("instagram | thapar.sports | Sports day broadcast: events schedule out", "instagram"),
    ("instagram | thapar.cultural | Open mic next Friday, walk-ins welcome", "instagram"),
]

SPAM_TEMPLATES: List[Tuple[str, str]] = [
    ("whatsapp | {phone} | Congrats! You won ₹50,000 in JioRewards. Click https://bit.ly/jio-prize", "whatsapp"),
    ("whatsapp | {phone} | KYC update urgent. Click http://hdfk-secure.in to avoid block", "whatsapp"),
    ("whatsapp | {phone} | Loan approved ₹5L instant. No CIBIL check. WhatsApp YES", "whatsapp"),
    ("whatsapp | {phone} | Hot girls in your city tonight. Click here to chat", "whatsapp"),
    ("whatsapp | {phone} | Crypto investment 10x guaranteed. WhatsApp now", "whatsapp"),
    ("whatsapp | BX-PROMO | FLAT 70% OFF on Bata. Use code SUMMER70. Limited stock", "whatsapp"),
    ("whatsapp | TM-OFFER | Recharge ₹199 get ₹399 cashback. Click bit.ly/airtl-back", "whatsapp"),
    ("whatsapp | {phone} | I am Singapore investor, will give you ₹5 cr, share details", "whatsapp"),
    ("whatsapp | {phone} | WORK FROM HOME ₹2000/day. WhatsApp HI", "whatsapp"),
    ("whatsapp | AD-DAILYDEALS | Smartwatch ₹499 only today click http://deal.ly/sw", "whatsapp"),
    ("whatsapp | {phone} | Your Aadhaar will be deactivated, click http://aadr-fix.in", "whatsapp"),
    ("whatsapp | {phone} | Earn ₹1000 daily promoting our products, WhatsApp START", "whatsapp"),
    ("instagram | insta.giveaway0982 | You're our chosen winner! Send your bank details to claim", "instagram"),
    ("instagram | crypto.bull.999 | Triple your money in 24 hrs. DM admin", "instagram"),
    ("instagram | weight.loss.now | Lose 10kg in 7 days, no diet, click bio link", "instagram"),
    ("instagram | followers.4.you | Get 10k followers free, link in bio", "instagram"),
    ("instagram | cheap.electronics | iPhone 15 ₹19,999 limited stock click DM", "instagram"),
    ("instagram | scammer.finance.guru | I made 50L last month, you can too. DM for course", "instagram"),
    ("instagram | fake.recruiter01 | Internship offer, send your bank details to confirm", "instagram"),
    ("slack | external-bot | Earn $5000/mo working from home. Apply now.", "slack"),
    ("slack | spam-channel | Click this link to validate your slack identity", "slack"),
    ("slack | unknown.user | Hi, I'm a recruiter from XYZ, please share your bank details", "slack"),
    ("slack | external-bot | you've been selected for a $1000 gift card click", "slack"),
    ("gmail | winner@lottery-india.org | CONGRATS!!! You won a lottery of ₹25 lakhs. Click claim", "gmail"),
    ("gmail | support@hdfbank-secure.com | ACCOUNT BLOCKED click here to verify", "gmail"),
    ("gmail | ceo@nigerianprince.cm | I have $10M for you, send your details", "gmail"),
    ("gmail | care@phshng.in | Update your AADHAAR online, click to avoid suspension", "gmail"),
    ("gmail | promo@dailydeals.in | FLAT 90% off on everything click before timer ends", "gmail"),
    ("gmail | bestoffers@deals4u.cn | Buy 1 get 5 free. Limited stock!! click", "gmail"),
    ("gmail | crypto@get-rich.io | Bitcoin 5x in 7 days, invest now", "gmail"),
    ("gmail | seo@spamhouse.ru | We can rank your site #1 on google, just $99", "gmail"),
    ("gmail | pharma@cheap-pills.org | Generic Viagra 70% off, no prescription", "gmail"),
    ("gmail | loans@instant-cash.in | Pre-approved loan ₹10 lakh, no docs", "gmail"),
    ("gmail | claim@you-won.in | FINAL NOTICE: claim your ₹5,00,000 prize NOW", "gmail"),
    ("gmail | admin@sketchy-site.tk | Your inbox is full, click to upgrade", "gmail"),
]


# Drafts — short, polite, deterministic. Used as the supervised target for the
# template-based reply head.
DRAFTS = [
    "On it - will push by tonight.",
    "Confirmed. See you at the time.",
    "Got it, will pay this evening.",
    "Yes please, thanks for the heads up.",
    "Will check and revert in 10 min.",
    "Sending the screenshot now.",
    "Done. Closing the loop today.",
    "Yes, I'm in. Lock it.",
    "Will be there by 8:15 sharp.",
    "Acknowledged. Thanks.",
]


HANDLES = ["manish_dsa", "aanya.codes", "kabir.designs", "riya.paints", "rohan.dev", "anu.creates", "mira.snaps"]


def _render(template: str) -> str:
    name = random.choice(NAMES)
    grp = random.choice(PROJECT_GROUPS)
    handle = random.choice(HANDLES)
    phone = random.choice(SPAM_NUMBERS)
    return template.format(n=name, grp=grp, handle=handle, phone=phone)


def _pick_urgency(label: str) -> Tuple[float, float]:
    if label == "ACTIONABLE":
        return random.uniform(0.65, 0.97), random.uniform(0.65, 0.97)
    if label == "BROADCAST":
        return random.uniform(0.10, 0.30), random.uniform(0.05, 0.20)
    if label == "SPAM":
        return random.uniform(0.01, 0.15), random.uniform(0.01, 0.15)
    return random.uniform(0.10, 0.45), random.uniform(0.20, 0.65)  # SOCIAL


def _emit(template_pool: List[Tuple[str, str]], label: str, n: int) -> List[dict]:
    rows: List[dict] = []
    for _ in range(n):
        tpl, surface = random.choice(template_pool)
        text = _render(tpl)
        urgency, self_rel = _pick_urgency(label)
        draft = random.choice(DRAFTS) if label == "ACTIONABLE" else ""
        rows.append({
            "input": text,
            "label": label,
            "urgency": round(urgency, 2),
            "self_relevance": round(self_rel, 2),
            "draft": draft,
            "surface": surface,
            "provenance": "synthetic",
        })
    return rows


def build(n_total: int = 500, seed: int = 42) -> List[dict]:
    random.seed(seed)
    # Class distribution: ACTIONABLE 35%, SOCIAL 30%, BROADCAST 20%, SPAM 15%.
    n_actionable = int(n_total * 0.35)
    n_social = int(n_total * 0.30)
    n_broadcast = int(n_total * 0.20)
    n_spam = n_total - n_actionable - n_social - n_broadcast
    rows = (
        _emit(ACTIONABLE_TEMPLATES, "ACTIONABLE", n_actionable)
        + _emit(SOCIAL_TEMPLATES, "SOCIAL", n_social)
        + _emit(BROADCAST_TEMPLATES, "BROADCAST", n_broadcast)
        + _emit(SPAM_TEMPLATES, "SPAM", n_spam)
    )
    random.shuffle(rows)
    return rows


def write(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main() -> None:
    out = Path(__file__).parent / "comms_train_synthetic.jsonl"
    rows = build(n_total=500)
    write(out, rows)
    print(f"wrote {len(rows)} rows to {out}")


if __name__ == "__main__":
    main()
