"""All on-screen words in Hindi and English. Change text here, not in app.py."""

LANGS = ["हिंदी", "English"]

# key: (English, Hindi)
T = {
    "app_sub": ("Follow the stolen money: add the bank data, check it, get a freeze-first list.",
                "चोरी हुए पैसे का पीछा करें: बैंक का डेटा डालें, जाँचें, और 'पहले किसे फ्रीज़ करें' की सूची पाएँ।"),
    "step1": ("1 · Add data", "1 · डेटा डालें"), "step2": ("2 · Check", "2 · जाँचें"), "step3": ("3 · Result", "3 · नतीजा"),
    "lang": ("Language", "भाषा"),
    "start_over": ("Start again", "फिर से शुरू करें"),
    "demo_btn": ("Try with made-up demo data", "डेमो (नकली) डेटा से आज़माएँ"),
    "demo_note": ("Demo data is made up. No real person or bank data.", "डेमो डेटा नकली है। इसमें कोई असली व्यक्ति या बैंक डेटा नहीं है।"),
    "upload_title": ("Drop the files you got from the banks here", "बैंकों से मिली फाइलें यहाँ डालें"),
    "upload_help": ("Excel, CSV or PDF (with selectable text). You can add many files together. TraceNet works out what each file is.",
                    "Excel, CSV या PDF (जिसमें टेक्स्ट चुना जा सके)। कई फाइलें एक साथ डाल सकते हैं। हर फाइल क्या है, यह TraceNet खुद पहचानेगा।"),
    "what_files": ("Which files can I use?", "कौन-सी फाइलें चल सकती हैं?"),
    "what_files_body": (
        "- **Transaction table**: one row per payment (from, to, amount, date).\n"
        "- **Bank statement**: one account's statement (date, narration, debit, credit). Tell us whose statement it is.\n"
        "- **Complaints**: the NCRP list (victim account, amount, date, transaction id).\n"
        "- **Account details** (optional): bank, mobile, device, IP, account opening date. Helps to find gangs.\n\n"
        "No complaint file? Add one by hand below.",
        "- **लेन-देन की तालिका**: हर पंक्ति में एक भुगतान (किससे, किसे, रकम, तारीख)।\n"
        "- **बैंक स्टेटमेंट**: एक खाते का स्टेटमेंट (तारीख, विवरण, डेबिट, क्रेडिट)। बताना होगा कि यह किसका है।\n"
        "- **शिकायतें**: NCRP की सूची (पीड़ित का खाता, रकम, तारीख, ट्रांज़ैक्शन आईडी)।\n"
        "- **खाता-विवरण** (ज़रूरी नहीं): बैंक, मोबाइल, डिवाइस, IP, खाता खुलने की तारीख। गिरोह पकड़ने में मदद करता है।\n\n"
        "शिकायत की फाइल नहीं है? नीचे हाथ से जोड़ें।"),
    "template_btn": ("Download a blank Excel template", "खाली Excel टेम्पलेट डाउनलोड करें"),
    "manual_title": ("Add a complaint by hand", "शिकायत हाथ से जोड़ें"),
    "m_victim": ("Victim's account number", "पीड़ित का खाता नंबर"), "m_amount": ("Amount lost (Rs)", "गई हुई रकम (रु.)"),
    "m_date": ("Date of fraud", "धोखाधड़ी की तारीख"), "m_time": ("Time of fraud (HH:MM)", "धोखाधड़ी का समय (HH:MM)"),
    "m_ref": ("Transaction id(s), optional (comma separated)", "ट्रांज़ैक्शन आईडी, ज़रूरी नहीं (कॉमा से अलग)"),
    "m_add": ("Add this complaint", "यह शिकायत जोड़ें"), "m_added": ("Complaints added by hand", "हाथ से जोड़ी गई शिकायतें"),
    "m_bad": ("Please fill the victim account, amount and a valid time.", "कृपया पीड़ित का खाता, रकम और सही समय भरें।"),
    "files_found": ("Files read", "पढ़ी गई फाइलें"),
    "type_is": ("This file is a", "यह फाइल है"),
    "kind_transactions": ("Transaction table", "लेन-देन की तालिका"), "kind_statement": ("Bank statement", "बैंक स्टेटमेंट"),
    "kind_complaints": ("Complaints", "शिकायतें"), "kind_accounts": ("Account details", "खाता-विवरण"),
    "sure": ("Understood the columns", "कॉलम समझ लिए"), "check_cols": ("Please check the columns", "कृपया कॉलम जाँच लें"),
    "cols_title": ("Which column is which? (change only if wrong)", "कौन-सा कॉलम क्या है? (गलत हो तभी बदलें)"),
    "none_opt": ("— not in this file —", "— इस फाइल में नहीं है —"),
    "preview": ("First rows of the file", "फाइल की शुरुआती पंक्तियाँ"),
    "owner_q": ("Whose statement is this? (account number)", "यह किसका स्टेटमेंट है? (खाता नंबर)"),
    "owner_help": ("Found in the file if possible. Needed so money in/out can be matched to this account.",
                   "फाइल से मिल जाए तो अपने आप भर जाता है। ज़रूरी है ताकि आना-जाना इसी खाते से जुड़ सके।"),
    "bank_q": ("Bank (optional)", "बैंक (ज़रूरी नहीं)"),
    "remove": ("Remove this file", "यह फाइल हटाएँ"),
    "to_check": ("Next: check my data  →", "आगे: मेरा डेटा जाँचें  →"),
    "need_file": ("Add at least one file (or try the demo data).", "कम से कम एक फाइल डालें (या डेमो डेटा आज़माएँ)।"),
    "check_title": ("Is this what you expected?", "क्या यह वही है जो आप सोच रहे थे?"),
    "c_tx": ("Payments read", "पढ़े गए भुगतान"), "c_acc": ("Accounts", "खाते"), "c_comp": ("Complaints", "शिकायतें"),
    "c_range": ("Dates covered", "तारीखें"), "c_cash": ("Cash-out points", "कैश-आउट बिंदु"),
    "no_complaint": ("No complaint found. Go back and add one by hand or add the complaints file.",
                     "कोई शिकायत नहीं मिली। पीछे जाकर हाथ से जोड़ें या शिकायत की फाइल डालें।"),
    "link_title": ("Join names / UPI ids to account numbers (optional)", "नाम / UPI id को खाता नंबर से जोड़ें (ज़रूरी नहीं)"),
    "link_help": ("In statements the other side is often shown as a name or UPI id. If you know its account number, type it here and the trail will join up.",
                  "स्टेटमेंट में सामने वाला अक्सर नाम या UPI id के रूप में दिखता है। उसका खाता नंबर पता हो तो यहाँ लिखें, रास्ता जुड़ जाएगा।"),
    "col_party": ("Name / UPI id in statement", "स्टेटमेंट में नाम / UPI id"), "col_times": ("Times", "बार"),
    "col_amt": ("Total (Rs)", "कुल (रु.)"), "col_same": ("Same as account number", "यही खाता नंबर है"),
    "go": ("Start analysis  →", "विश्लेषण शुरू करें  →"), "back": ("←  Back", "←  पीछे"),
    "note_rows_dropped": ("{n} of {total} rows in {name} were skipped (missing date, amount or account).",
                          "{name} की {total} में से {n} पंक्तियाँ छोड़ दी गईं (तारीख, रकम या खाता नहीं मिला)।"),
    "note_unknown_party": ("{n} entries in {name} show only a name or UPI id, not an account number. You can join them below.",
                           "{name} में {n} प्रविष्टियों में सिर्फ नाम या UPI id है, खाता नंबर नहीं। इन्हें नीचे जोड़ सकते हैं।"),
    "note_no_time": ("The data has dates but no time of day. Order of payments within the same day is a best guess.",
                     "डेटा में सिर्फ तारीख है, समय नहीं। एक ही दिन के भुगतानों का क्रम अनुमान से है।"),
    "note_ref_not_found": ("Complaint {cid}: the transaction id was not found in the data, so all payments of the victim after the fraud time are followed.",
                           "शिकायत {cid}: ट्रांज़ैक्शन आईडी डेटा में नहीं मिली, इसलिए धोखाधड़ी के बाद पीड़ित के सभी भुगतान देखे जाएँगे।"),
    "note_time_guessed": ("Complaint {cid}: fraud time was missing; used the victim's first payment in the data.",
                          "शिकायत {cid}: धोखाधड़ी का समय नहीं था; डेटा में पीड़ित का पहला भुगतान लिया गया।"),
    "note_complaint_skipped": ("Complaint {cid} was skipped: victim account, amount or time is missing.",
                               "शिकायत {cid} छोड़ दी गई: पीड़ित का खाता, रकम या समय नहीं मिला।"),
    "note_victim_not_in_tx": ("Complaint {cid}: no payments from account {acct} found in the data. Add the victim's statement or the first bank's reply.",
                              "शिकायत {cid}: खाता {acct} से कोई भुगतान डेटा में नहीं मिला। पीड़ित का स्टेटमेंट या पहले बैंक का जवाब जोड़ें।"),
    "err_scanned_pdf": ("This PDF is a scanned picture, so the text cannot be read. Ask the bank for Excel/CSV, or use an OCR tool first.",
                        "यह PDF स्कैन की हुई तस्वीर है, इसका टेक्स्ट नहीं पढ़ा जा सकता। बैंक से Excel/CSV माँगें, या पहले OCR टूल चलाएँ।"),
    "err_bad_type": ("{name}: this file type is not supported. Use .xlsx, .xls, .csv or .pdf.", "{name}: यह फाइल प्रकार नहीं चलता। .xlsx, .xls, .csv या .pdf दें।"),
    "err_no_table": ("{name}: could not find a table of data in this file.", "{name}: इस फाइल में डेटा की तालिका नहीं मिली।"),
    "err_no_owner": ("{name}: please type whose statement this is (account number).", "{name}: कृपया बताएँ कि यह किसका स्टेटमेंट है (खाता नंबर)।"),
    "err_no_transactions": ("No payments found. Add a transaction table or a bank statement.", "कोई भुगतान नहीं मिला। लेन-देन की तालिका या बैंक स्टेटमेंट डालें।"),
    "err_read": ("Could not read {name}: {why}", "{name} पढ़ी नहीं जा सकी: {why}"),
    # results
    "pick": ("Pick a complaint", "शिकायत चुनें"), "lost": ("Money lost", "गई हुई रकम"),
    "in_hour": ("Reported inside the first hour: act now.", "पहले घंटे में दर्ज: अभी कार्रवाई करें।"),
    "late": ("Reported {h:.0f} hours after the fraud. Most money has probably moved on, so focus on accounts that still hold some.",
             "धोखाधड़ी के {h:.0f} घंटे बाद दर्ज हुई। ज़्यादातर पैसा आगे जा चुका होगा, इसलिए उन खातों पर ध्यान दें जिनमें अभी पैसा है।"),
    "when": ("Look at the situation this many minutes after the fraud", "धोखाधड़ी के इतने मिनट बाद की स्थिति देखें"),
    "when_help": ("Drag left to see how much more could have been saved by acting earlier.", "बाएँ खींचें और देखें कि जल्दी कार्रवाई से कितना और बच सकता था।"),
    "k_held": ("Still inside bank accounts", "अभी बैंक खातों में"), "k_held_h": ("Money you can still try to freeze", "इसे अभी भी फ्रीज़ कराया जा सकता है"),
    "k_cash": ("Already taken out", "निकल चुका"), "k_cash_h": ("Left the banks through ATM, wallet or crypto", "ATM, वॉलेट या क्रिप्टो से बैंक से बाहर"),
    "k_acc": ("Accounts involved", "शामिल खाते"),
    "todo": ("What to do now", "अभी क्या करें"),
    "tab_trail": ("Money trail", "पैसे का रास्ता"), "tab_act": ("Who to act on", "किस पर कार्रवाई"), "tab_sus": ("Suspicious accounts & gangs", "संदिग्ध खाते और गिरोह"),
    "tab_ask": ("Requests to banks", "बैंकों को अनुरोध"), "tab_rep": ("Report", "रिपोर्ट"), "tab_more": ("More tools", "और औज़ार"),
    "read_pic": ("How to read the picture", "तस्वीर कैसे पढ़ें"),
    "read_pic_body": ("⭐ victim · ⚪ bank account · 🔶 cash-out point · **redder** = more suspicious · **thicker line** = more stolen money · **left to right** = each step. Hover for details.",
                      "⭐ पीड़ित · ⚪ बैंक खाता · 🔶 कैश-आउट बिंदु · **ज़्यादा लाल** = ज़्यादा संदिग्ध · **मोटी रेखा** = ज़्यादा चोरी का पैसा · **बाएँ से दाएँ** = हर कदम। ब्योरे के लिए माउस ले जाएँ।"),
    "nothing_moved": ("Nothing has moved onward yet at this time.", "इस समय तक पैसा आगे नहीं गया है।"),
    "act_cap": ("Accounts that still hold stolen money come first.", "जिन खातों में अभी चोरी का पैसा है वे सबसे ऊपर हैं।"),
    "dl_bank": ("Download the file for banks (.csv)", "बैंकों के लिए फाइल डाउनलोड करें (.csv)"),
    "sus_cap": ("'Mule' accounts only pass stolen money along. Higher score = more suspicious.", "'म्यूल' खाते सिर्फ चोरी का पैसा आगे बढ़ाते हैं। ज़्यादा स्कोर = ज़्यादा संदिग्ध।"),
    "sus_none": ("Scores need payments between several accounts. Not enough data to score.", "स्कोर के लिए कई खातों के बीच भुगतान चाहिए। स्कोर लायक डेटा नहीं है।"),
    "gang_cap": ("Groups of accounts that look like one gang (same phone, device, IP, or paying the same place).",
                 "खातों के समूह जो एक गिरोह जैसे दिखते हैं (वही फोन, डिवाइस, IP, या एक ही जगह पैसा भेजना)।"),
    "gang_none": ("No gang found with this data.", "इस डेटा में कोई गिरोह नहीं मिला।"),
    "gang_n": ("Gang {i} ({n} accounts)", "गिरोह {i} ({n} खाते)"),
    "wave_cap": ("Bank replies arrive in waves. Grey accounts marked '?' hold stolen money but their bank has not replied yet.",
                 "बैंकों के जवाब किस्तों में आते हैं। '?' वाले स्लेटी खातों में चोरी का पैसा है पर उनके बैंक का जवाब अभी नहीं आया।"),
    "wave": ("Wave of bank replies", "बैंक जवाब की किस्त"), "w_known": ("Accounts known so far", "अब तक ज्ञात खाते"), "w_banks": ("Banks to ask right now", "अभी जिन बैंकों से पूछना है"),
    "dl_rep": ("Download the report (.md)", "रिपोर्ट डाउनलोड करें (.md)"),
    "wl_title": ("Shared list of risky accounts for banks", "बैंकों के लिए जोखिम वाले खातों की साझा सूची"), "dl_wl": ("Download the list (.csv)", "सूची डाउनलोड करें (.csv)"),
    "pre_title": ("Check an account before sending money", "पैसा भेजने से पहले खाता जाँचें"),
    "pre_cap": ("What a banking app could ask before a transfer. It warns or delays; it never silently blocks.", "बैंकिंग ऐप ट्रांसफर से पहले यही पूछ सकता है। यह चेतावनी देता है या रोकता है, चुपचाप ब्लॉक नहीं करता।"),
    "pre_acc": ("Account the money is going to", "जिस खाते में पैसा जा रहा है"), "pre_use": ("Use the shared list of risky accounts", "जोखिम वाले खातों की साझा सूची इस्तेमाल करें"),
    "risk_HIGH": ("HIGH RISK", "ज़्यादा जोखिम"), "risk_MEDIUM": ("MEDIUM RISK", "मध्यम जोखिम"), "risk_LOW": ("LOW RISK", "कम जोखिम"),
    "test_title": ("Accuracy test (demo data only)", "सटीकता जाँच (सिर्फ डेमो डेटा)"),
    "test_body": ("On made-up data: found {tp} of {tot} planted mule accounts, {fp} wrongly accused.", "नकली डेटा पर: {tot} में से {tp} म्यूल खाते मिले, {fp} गलत पकड़े गए।"),
    "disclaimer": ("TraceNet gives leads for investigators, not proof. Investigators and banks decide.", "TraceNet जाँचकर्ताओं को सुराग देता है, सबूत नहीं। फैसला जाँचकर्ता और बैंक करते हैं।"),
}

ROLE = {   # friendly column names: role -> (English, Hindi)
    "txn_id": ("Transaction id / UTR", "ट्रांज़ैक्शन आईडी / UTR"), "ts": ("Date and time", "तारीख और समय"), "src": ("Paid from (account)", "किस खाते से गया"),
    "dst": ("Paid to (account)", "किस खाते में गया"), "amount": ("Amount", "रकम"), "channel": ("Mode (UPI/IMPS/ATM…)", "माध्यम (UPI/IMPS/ATM…)"),
    "date": ("Date", "तारीख"), "time": ("Time (if separate)", "समय (अलग हो तो)"), "narration": ("Narration / details", "विवरण / नैरेशन"),
    "ref": ("Reference no.", "रेफरेंस नंबर"), "debit": ("Debit (money out)", "डेबिट (पैसा गया)"), "credit": ("Credit (money in)", "क्रेडिट (पैसा आया)"),
    "drcr": ("Dr/Cr marker (if one amount column)", "Dr/Cr चिह्न (एक ही रकम कॉलम हो तो)"), "balance": ("Balance", "बैलेंस"),
    "complaint_id": ("Complaint / acknowledgement no.", "शिकायत / पावती नंबर"), "victim_account": ("Victim account", "पीड़ित का खाता"),
    "fraud_ts": ("Date-time of fraud", "धोखाधड़ी की तारीख-समय"), "reported_ts": ("Date-time reported", "शिकायत की तारीख-समय"),
    "txn_ref": ("Transaction id of the victim's payment", "पीड़ित के भुगतान की ट्रांज़ैक्शन आईडी"), "first_mule": ("First receiving account", "पैसा पाने वाला पहला खाता"),
    "bank": ("Bank", "बैंक"), "account_id": ("Account number", "खाता नंबर"), "kyc_age_days": ("Account age in days", "खाते की उम्र (दिन)"),
    "open_date": ("Account opening date", "खाता खुलने की तारीख"), "device_id": ("Device id", "डिवाइस आईडी"), "phone": ("Mobile number", "मोबाइल नंबर"), "ip": ("IP address", "IP पता"),
}


def make_t(lang: str):
    i = 1 if lang == LANGS[0] else 0

    def t(key, **kw):
        s = T[key][i]
        return s.format(**kw) if kw else s

    def role(r):
        return ROLE.get(r, (r, r))[i]

    return t, role


T.update({
    "view_one": ("One complaint at a time", "एक-एक शिकायत"), "view_links": ("Connections between complaints", "शिकायतों के बीच जुड़ाव"),
    "lk_one": ("Only one complaint in the data, so there is nothing to connect yet. Add more complaints.", "डेटा में सिर्फ एक शिकायत है, इसलिए जोड़ने को कुछ नहीं। और शिकायतें जोड़ें।"),
    "lk_headline": ("{g} case group(s) found among {n} complaints. {s} complaint(s) stand alone.", "{n} शिकायतों में {g} केस-समूह मिले। {s} शिकायतें अकेली हैं।"),
    "lk_none": ("No complaints look connected with this data. Add more complaints or bank statements to find links.", "इस डेटा में कोई शिकायतें जुड़ी नहीं दिखीं। जुड़ाव पाने के लिए और शिकायतें या बैंक स्टेटमेंट जोड़ें।"),
    "lk_how": ("How are complaints linked?", "शिकायतें कैसे जोड़ी जाती हैं?"),
    "lk_how_body": (
        "TraceNet gives every pair of complaints a **score** from the evidence. It is not a yes/no rule: more evidence, higher score.\n\n"
        "- the **same account** received stolen money from both (more points if it looks like a mule)\n"
        "- the **same cash-out point** (same ATM / wallet / crypto account)\n"
        "- accounts that are different but sit in the **same gang ring** (same phone, device or IP)\n"
        "- one victim's account was used to **pass on** the other's money\n"
        "- both frauds happened within a day (a small extra push only)\n\n"
        "**Strong / Probable** links join complaints into one *case group*. **Possible (weak)** links are shown but do not join groups. "
        "A link is a lead for the investigator, not proof.",
        "TraceNet हर दो शिकायतों को सबूत के आधार पर एक **स्कोर** देता है। यह हाँ/ना का नियम नहीं है: जितना ज़्यादा सबूत, उतना ऊँचा स्कोर।\n\n"
        "- **एक ही खाते** में दोनों का चोरी का पैसा आया (म्यूल जैसा लगे तो ज़्यादा अंक)\n"
        "- **एक ही कैश-आउट बिंदु** (वही ATM / वॉलेट / क्रिप्टो खाता)\n"
        "- अलग खाते, पर **एक ही गिरोह-रिंग** में (वही फोन, डिवाइस या IP)\n"
        "- एक पीड़ित के खाते से दूसरे का पैसा **आगे गया**\n"
        "- दोनों धोखाधड़ी एक दिन के भीतर हुईं (सिर्फ थोड़ा-सा अतिरिक्त वज़न)\n\n"
        "**पक्का / संभावित** जुड़ाव शिकायतों को एक *केस-समूह* में बाँधते हैं। **कमज़ोर संभावना** दिखती है पर समूह नहीं बनाती। "
        "जुड़ाव जाँचकर्ता के लिए सुराग है, सबूत नहीं।"),
    "lk_tab_sum": ("Summary & new-complaint alert", "सारांश और नई शिकायत चेतावनी"), "lk_tab_net": ("Network picture", "नेटवर्क चित्र"),
    "lk_tab_shared": ("Shared accounts & money split", "साझा खाते और पैसे का बँटवारा"), "lk_tab_time": ("Time pattern", "समय का पैटर्न"),
    "lk_tab_rep": ("Combined report & bank file", "संयुक्त रिपोर्ट और बैंक फाइल"),
    "lk_pick_group": ("Pick a case group", "केस-समूह चुनें"),
    "lk_group_sum": ("{n} complaints · ₹{lost} lost in total · linked through {k} shared account(s){ex} · ₹{inside} still inside accounts.",
                     "{n} शिकायतें · कुल ₹{lost} गए · {k} साझा खाते{ex} से जुड़ी · ₹{inside} अभी खातों में।"),
    "lk_group_ex": (" and {e} shared cash-out point(s)", " और {e} साझा कैश-आउट बिंदु"),
    "lk_why": ("Why these complaints are linked", "ये शिकायतें क्यों जुड़ीं"), "col_a": ("Complaint A", "शिकायत A"), "col_b": ("Complaint B", "शिकायत B"),
    "col_level": ("Strength", "मज़बूती"), "col_score": ("Score", "स्कोर"), "col_reason": ("Evidence", "सबूत"),
    "lvl_strong": ("Strong", "पक्का"), "lvl_probable": ("Probable", "संभावित"), "lvl_possible": ("Possible (weak)", "कमज़ोर संभावना"),
    "lk_r_accts": ("shares {n} account(s): {names}", "{n} खाते साझा: {names}"), "lk_r_exit": ("same cash-out point: {names}", "वही कैश-आउट बिंदु: {names}"),
    "lk_r_ring": ("accounts in the same gang ring ({n})", "एक ही गिरोह-रिंग के खाते ({n})"),
    "lk_r_victim": ("victim account {acct} was used to pass on the other complaint's money", "पीड़ित का खाता {acct} दूसरी शिकायत का पैसा आगे भेजने में इस्तेमाल हुआ"),
    "lk_r_time": ("frauds {h:.0f} hours apart", "धोखाधड़ी में {h:.0f} घंटे का अंतर"),
    "lk_alone": ("Complaints not linked to any other (so far)", "जो शिकायतें अभी किसी से नहीं जुड़ीं"),
    "alert_title": ("New complaint check", "नई शिकायत की जाँच"),
    "alert_pick": ("Treat this complaint as the newly arrived one", "इस शिकायत को नई आई हुई मानें"),
    "alert_yes": ("⚠ This complaint is linked to {n} earlier complaint(s) ({gid}). Act on the shared accounts first: ₹{inside} is still inside them.",
                  "⚠ यह शिकायत {n} पुरानी शिकायतों से जुड़ी है ({gid})। पहले साझा खातों पर कार्रवाई करें: इनमें ₹{inside} अभी अंदर है।"),
    "alert_no": ("No link with earlier complaints so far. With the data you have, this looks like a stand-alone case.",
                 "पुरानी शिकायतों से अब तक कोई जुड़ाव नहीं। आपके डेटा के हिसाब से यह अकेला मामला लगता है।"),
    "alert_shared": ("Shared accounts", "साझा खाते"),
    "lk_banner": ("This complaint belongs to {gid} together with {n} other complaint(s). Open 'Connections between complaints' to see how.",
                  "यह शिकायत {gid} का हिस्सा है, साथ में {n} और शिकायतें। कैसे, यह देखने के लिए 'शिकायतों के बीच जुड़ाव' खोलें।"),
    "lk_net_cap": ("Squares = complaints · circles = bank accounts · diamonds = cash-out points · big = used by many complaints · redder = more suspicious · "
                   "dashed red line = linked through the same gang ring without sharing an account.",
                   "चौकोर = शिकायतें · गोले = बैंक खाते · हीरे = कैश-आउट बिंदु · बड़ा = कई शिकायतों में · ज़्यादा लाल = ज़्यादा संदिग्ध · "
                   "लाल टूटी रेखा = एक ही गिरोह-रिंग से जुड़ाव, बिना साझा खाते के।"),
    "lk_show_all": ("Also show accounts used by only one complaint", "सिर्फ एक शिकायत वाले खाते भी दिखाएँ"),
    "lk_all_groups": ("Show all case groups together", "सभी केस-समूह साथ दिखाएँ"),
    "lk_sh_cap": ("Accounts that got stolen money from 2 or more complaints. Freeze these first: one action helps many victims.",
                  "ऐसे खाते जिनमें 2 या ज़्यादा शिकायतों का चोरी का पैसा आया। इन्हें पहले फ्रीज़ कराएँ: एक कार्रवाई से कई पीड़ितों को फायदा।"),
    "col_acc": ("Account", "खाता"), "col_bank": ("Bank", "बैंक"), "col_n": ("Complaints", "शिकायतें"), "col_which": ("Which complaints", "कौन-सी शिकायतें"),
    "col_total": ("Stolen money received (Rs)", "मिला चोरी का पैसा (रु.)"), "col_inside2": ("Still inside (Rs)", "अभी अंदर (रु.)"),
    "col_mule": ("Mule score", "म्यूल स्कोर"), "col_firstuse": ("First used", "पहली बार"), "col_lastuse": ("Last used", "आखिरी बार"),
    "col_fh": ("First receiver in", "पहला पाने वाला (शिकायतों में)"),
    "lk_exits": ("Cash-out points used by more than one complaint", "एक से ज़्यादा शिकायतों में इस्तेमाल हुए कैश-आउट बिंदु"),
    "lk_split": ("Whose money is it? Split of each shared account", "यह किसका पैसा है? हर साझा खाते का बँटवारा"),
    "lk_split_cap": ("When one account holds money from several complaints, each complaint's share is counted separately, in proportion to what it put in. Nothing is counted twice.",
                     "जब एक खाते में कई शिकायतों का पैसा हो, तो हर शिकायत का हिस्सा अलग गिना जाता है, जितना उसने डाला उसी अनुपात में। कुछ भी दो बार नहीं गिना जाता।"),
    "lk_split_tbl": ("Detail", "ब्योरा"), "col_compl": ("Complaint", "शिकायत"),
    "tm_window": ("Active between", "सक्रिय रहे"), "tm_gap": ("Average gap between complaints", "शिकायतों के बीच औसत अंतर"), "tm_gap_u": ("{h:.1f} hours", "{h:.1f} घंटे"),
    "tm_speed": ("Median time to first cash-out", "पहले कैश-आउट तक औसत समय"), "tm_speed_u": ("{m:.0f} min", "{m:.0f} मिनट"),
    "tm_night": ("Frauds between 10pm and 6am", "रात 10 से सुबह 6 के बीच की धोखाधड़ी"),
    "tm_ins_fast": ("Money was cashed out within about {m:.0f} minutes. Banks must be asked inside the first hour.", "पैसा लगभग {m:.0f} मिनट में निकल गया। बैंकों को पहले घंटे में ही कहना होगा।"),
    "tm_ins_night": ("Most frauds happened at night, when banks and victims react slowly. Keep a night-time freeze contact ready.", "ज़्यादातर धोखाधड़ी रात में हुई, जब बैंक और पीड़ित देर से प्रतिक्रिया देते हैं। रात का फ्रीज़ संपर्क तैयार रखें।"),
    "tm_ins_gap": ("The gang struck again every {h:.1f} hours on average.", "गिरोह ने औसतन हर {h:.1f} घंटे में फिर वार किया।"),
    "tm_hours": ("When the frauds started (dark bars = night)", "धोखाधड़ी कब शुरू हुई (गहरी पट्टी = रात)"),
    "tm_tl": ("Timeline: when each shared account received stolen money", "समय-रेखा: हर साझा खाते में चोरी का पैसा कब आया"),
    "tm_tl_cap": ("★ = the moment each fraud started. Each dot = stolen money arriving; colour = which complaint; big dot = more money.",
                  "★ = हर धोखाधड़ी की शुरुआत। हर बिंदु = चोरी का पैसा आना; रंग = कौन-सी शिकायत; बड़ा बिंदु = ज़्यादा पैसा।"),
    "tm_new": ("New accounts the gang started using, per day", "गिरोह ने रोज़ कितने नए खाते इस्तेमाल करना शुरू किए"),
    "col_day": ("Day", "दिन"), "col_newacc": ("New accounts", "नए खाते"),
    "lk_banks": ("Banks involved (accounts)", "शामिल बैंक (खाते)"),
    "lk_dl_rep": ("Download combined report (.md)", "संयुक्त रिपोर्ट डाउनलोड करें (.md)"),
    "lk_dl_bank": ("Download one bank file for the whole case (.csv)", "पूरे केस की एक बैंक फाइल डाउनलोड करें (.csv)"),
    "lk_bank_cap": ("One row per account to act on, across all complaints in the case. Send each bank one request instead of many.",
                    "कार्रवाई वाले हर खाते की एक पंक्ति, केस की सभी शिकायतों को मिलाकर। हर बैंक को कई की जगह एक अनुरोध भेजें।"),
})


T.update({
    # ---- picture legends
    "fig_victim": ("Victim", "पीड़ित"), "fig_step": ("Step", "कदम"),
    "leg_victim": ("★ Victim (money was lost here)", "★ पीड़ित (यहाँ से पैसा गया)"),
    "leg_inside": ("Money still inside: can be frozen", "अभी पैसा अंदर है: फ्रीज़ हो सकता है"),
    "leg_passed": ("Passed on: account is now empty", "आगे भेज दिया: खाता अब खाली"),
    "leg_cash": ("Cash-out: money left the banks", "कैश-आउट: पैसा बैंक से बाहर गया"),
    "leg_unknown": ("? Bank has not replied yet", "? बैंक का जवाब अभी नहीं आया"),
    "hv_got": ("Stolen money received", "मिला चोरी का पैसा"), "hv_inside": ("Still inside", "अभी अंदर"), "hv_score": ("Suspicion score", "संदेह स्कोर"),
    # ---- glossary
    "gl_title": ("📖 Words used in this tool (open to read)", "📖 इस टूल में आने वाले शब्द (पढ़ने के लिए खोलें)"),
    "gl_body": (
        "- **Stolen money / tainted money**: the part of an account's balance that came from the victim. TraceNet assumes stolen money is spent first (cautious view).\n"
        "- **Step (hop)**: one transfer. Step 1 = first account that got money from the victim, Step 2 = the account that got it from Step 1, and so on.\n"
        "- **Mule account**: an account used only to receive money and pass it on, usually opened or rented for the fraud.\n"
        "- **Suspicion score (0–100)**: how much an account behaves like a mule. 0–39 low · 40–69 medium · 70–100 high. It is a lead, not proof.\n"
        "- **Freeze / lien**: asking the bank to hold the balance of an account. Only money still inside can be held.\n"
        "- **Cash-out point**: where money left the banks: ATM withdrawal, wallet (Paytm etc.), crypto exchange or plain cash.\n"
        "- **Golden hour**: the first hour after the fraud. If banks are asked inside it, much more money can be saved.\n"
        "- **Gang ring**: accounts that look run by the same people: same phone, device or IP, or paying the same beneficiary.\n"
        "- **Case group (CASE-1…)**: complaints that TraceNet thinks belong to the same gang.\n"
        "- **KYC**: the identity papers an account was opened with. A very new account used for big transfers is a warning sign.\n"
        "- **UTR / transaction id**: the reference number of one payment. It lets the bank find exactly that payment.\n"
        "- **Wave of bank replies**: banks answer in rounds. Each round shows more of the trail and tells you which bank to ask next.",
        "- **चोरी का पैसा**: खाते के बैलेंस का वह हिस्सा जो पीड़ित से आया। TraceNet मानता है कि चोरी का पैसा पहले खर्च होता है (सावधानी वाला नज़रिया)।\n"
        "- **कदम (hop)**: एक ट्रांसफर। कदम 1 = पीड़ित से पैसा पाने वाला पहला खाता, कदम 2 = कदम 1 से पैसा पाने वाला खाता, आदि।\n"
        "- **म्यूल खाता**: ऐसा खाता जो सिर्फ पैसा लेने और आगे भेजने के काम आता है, अक्सर धोखाधड़ी के लिए खोला या किराए पर लिया गया।\n"
        "- **संदेह स्कोर (0–100)**: खाता कितना म्यूल जैसा व्यवहार करता है। 0–39 कम · 40–69 मध्यम · 70–100 ज़्यादा। यह सुराग है, सबूत नहीं।\n"
        "- **फ्रीज़ / लिएन**: बैंक से खाते का बैलेंस रोकने को कहना। सिर्फ वही पैसा रुक सकता है जो अभी खाते में है।\n"
        "- **कैश-आउट बिंदु**: जहाँ पैसा बैंक से बाहर गया: ATM निकासी, वॉलेट (Paytm आदि), क्रिप्टो एक्सचेंज या नकद।\n"
        "- **गोल्डन आवर**: धोखाधड़ी के बाद का पहला घंटा। इसमें बैंक को कहा जाए तो बहुत ज़्यादा पैसा बच सकता है।\n"
        "- **गिरोह-रिंग**: खाते जो एक ही लोगों के चलाए लगते हैं: वही फोन, डिवाइस या IP, या एक ही लाभार्थी को पैसा।\n"
        "- **केस-समूह (CASE-1…)**: वे शिकायतें जिन्हें TraceNet एक ही गिरोह की मानता है।\n"
        "- **KYC**: पहचान के कागज़ जिनसे खाता खुला। बहुत नया खाता और बड़े ट्रांसफर, यह खतरे का संकेत है।\n"
        "- **UTR / ट्रांज़ैक्शन आईडी**: एक भुगतान का रेफरेंस नंबर। इससे बैंक ठीक वही भुगतान ढूँढ पाता है।\n"
        "- **बैंक जवाब की किस्त**: बैंक किस्तों में जवाब देते हैं। हर किस्त में रास्ता और खुलता है और पता चलता है कि अगला किस बैंक से पूछना है।"),
    "g3_help": ("How to read this page: ① the headline and three numbers tell you how bad it is · ② 'What to do now' tells you what to do first · ③ each tab has a picture with a one-line explanation above it and an action box below it.",
                "इस पेज को कैसे पढ़ें: ① हेडलाइन और तीन संख्याएँ बताती हैं कि मामला कितना बड़ा है · ② 'अभी क्या करें' बताता है कि पहले क्या करना है · ③ हर टैब में एक चित्र है, ऊपर एक पंक्ति में उसका मतलब और नीचे कार्रवाई का डिब्बा।"),
    "show_lbl": ("What this picture shows", "यह चित्र क्या दिखाता है"), "next_lbl": ("What to do next", "अब क्या करें"),
    "expl_lbl": ("What each number means", "हर नंबर का मतलब"), "more_detail": ("More detail", "और ब्योरा"),
    # ---- money trail
    "tr_show": ("Follow the stolen money from left to right. It starts with the victim (★), moves through bank accounts one step at a time, and ends where it was taken out. "
                "The number inside each circle is the order in which accounts received the money. The ₹ on each arrow is stolen money only.",
                "चोरी हुए पैसे को बाएँ से दाएँ देखें। यह पीड़ित (★) से शुरू होकर बैंक खातों से एक-एक कदम आगे जाता है और वहाँ खत्म होता है जहाँ से निकाला गया। "
                "हर गोले का नंबर बताता है कि खातों में पैसा किस क्रम में पहुँचा। तीर पर लिखा ₹ सिर्फ चोरी का पैसा है।"),
    "tr_victim_line": ("★ Victim {acct} lost ₹{amt} at {time}.", "★ पीड़ित {acct} के ₹{amt} {time} पर गए।"),
    "tr_inside": ("**{n}. {acct}** ({bank}) got ₹{recv} at {t}. **₹{held} is still inside**: ask the bank to freeze it now.",
                  "**{n}. {acct}** ({bank}) में {t} पर ₹{recv} आया। **₹{held} अभी अंदर है**: बैंक से अभी फ्रीज़ कराएँ।"),
    "tr_passed": ("**{n}. {acct}** ({bank}) got ₹{recv} at {t}{d}. Nothing is left inside; ask for its statement and KYC.",
                  "**{n}. {acct}** ({bank}) में {t} पर ₹{recv} आया{d}। अंदर कुछ नहीं बचा; इसका स्टेटमेंट और KYC माँगें।"),
    "tr_passed_d": (" and was passed on within {m:.0f} minutes", " और {m:.0f} मिनट के भीतर आगे भेज दिया गया"),
    "tr_unknown": ("**{n}. {acct}** ({bank}) got ₹{recv} at {t}. We do not know where it went next: ask this bank for the statement.",
                   "**{n}. {acct}** ({bank}) में {t} पर ₹{recv} आया। आगे कहाँ गया पता नहीं: इस बैंक से स्टेटमेंट माँगें।"),
    "tr_cash": ("**{n}. {acct}**: ₹{recv} was taken out at {t}. It cannot be frozen now; ask for ATM / wallet / exchange records (CCTV, KYC, device).",
                "**{n}. {acct}**: ₹{recv} {t} पर निकाला गया। अब फ्रीज़ नहीं हो सकता; ATM / वॉलेट / एक्सचेंज रिकॉर्ड (CCTV, KYC, डिवाइस) माँगें।"),
    "tr_warn": ("⚠ next to an account = it also behaves like a mule (see the tab 'Suspicious accounts & gangs').",
                "⚠ किसी खाते के आगे = वह म्यूल जैसा व्यवहार भी करता है (टैब 'संदिग्ध खाते और गिरोह' देखें)।"),
    "tr_next_inside": ("**{n} account(s) still hold ₹{amt}.** Send the freeze request to their banks now: the tab 'Who to act on' has the file for banks. Money still inside is the only part that can be returned.",
                       "**{n} खातों में अभी ₹{amt} है।** उनके बैंकों को अभी फ्रीज़ का अनुरोध भेजें: टैब 'किस पर कार्रवाई' में बैंकों के लिए फाइल है। जो पैसा अभी अंदर है, सिर्फ वही लौटाया जा सकता है।"),
    "tr_next_none": ("No stolen money is left inside the accounts we can see. Ask for the statements of accounts marked ?, get cash-out records (CCTV, KYC), and check the tab 'Connections between complaints' for other victims of the same gang.",
                     "जो खाते हमें दिख रहे हैं उनमें चोरी का पैसा नहीं बचा। जिन खातों पर ? है उनके स्टेटमेंट माँगें, कैश-आउट रिकॉर्ड (CCTV, KYC) लें, और उसी गिरोह के दूसरे पीड़ितों के लिए 'शिकायतों के बीच जुड़ाव' देखें।"),
    "tr_next_unknown": ("**{n} account(s) marked ? have an unknown next step.** Their banks have not replied yet: the tab 'Requests to banks' has the letters ready.",
                        "**{n} खातों पर ? है, यानी आगे का रास्ता अज्ञात।** उनके बैंकों का जवाब नहीं आया: टैब 'बैंकों को अनुरोध' में पत्र तैयार हैं।"),
    # ---- act / suspicious tables
    "act_show": ("The accounts the money passed through, in the order you should act. Accounts that still hold stolen money come first, then the more suspicious ones.",
                 "वे खाते जिनसे पैसा गुज़रा, उसी क्रम में जिसमें कार्रवाई करनी चाहिए। पहले वे जिनमें चोरी का पैसा अभी है, फिर ज़्यादा संदिग्ध।"),
    "act_cols": ("**Steps from victim** = how many transfers after the victim. **Suspicion score** = how much it looks like a mule (0–100). **What to do** = suggested action for the bank.",
                 "**पीड़ित से कदम** = पीड़ित के बाद कितने ट्रांसफर हुए। **संदेह स्कोर** = यह कितना म्यूल जैसा है (0–100)। **क्या करें** = बैंक के लिए सुझाई कार्रवाई।"),
    "act_next": ("Download the bank file and send it to each bank's nodal officer. Use the full account number from this table: the pictures show only the last 4 digits.",
                 "बैंक फाइल डाउनलोड करके हर बैंक के नोडल अधिकारी को भेजें। इस तालिका का पूरा खाता नंबर इस्तेमाल करें: चित्रों में सिर्फ आखिरी 4 अंक दिखते हैं।"),
    "sus_show": ("Accounts ranked by how much they behave like a mule. The reason for each score is written next to it.",
                 "खाते इस क्रम में कि वे कितना म्यूल जैसा व्यवहार करते हैं। हर स्कोर का कारण उसके बगल में लिखा है।"),
    "sus_scale": ("Score guide: 0–39 low · 40–69 medium · 70–100 high. A high score is a lead for investigation, never proof.",
                  "स्कोर गाइड: 0–39 कम · 40–69 मध्यम · 70–100 ज़्यादा। ज़्यादा स्कोर जाँच का सुराग है, सबूत नहीं।"),
    "sus_next": ("Check the accounts with a high score even if no money is inside now: they may be used again. Ask their banks for KYC and a transaction history.",
                 "ज़्यादा स्कोर वाले खातों को जाँचें, भले अभी उनमें पैसा न हो: वे दोबारा इस्तेमाल हो सकते हैं। उनके बैंकों से KYC और लेन-देन का इतिहास माँगें।"),
    # ---- waves
    "rd_show": ("Banks answer in rounds. This picture shows only what is known after the round you choose. Accounts marked ? got stolen money but their bank has not replied yet.",
                "बैंक किस्तों में जवाब देते हैं। यह चित्र चुनी गई किस्त तक की जानकारी दिखाता है। जिन खातों पर ? है उनमें चोरी का पैसा आया पर उनके बैंक का जवाब नहीं आया।"),
    "rd_next": ("Send the letters below to the banks listed. When they reply, add their statements (step 1) and the picture will grow by one more wave.",
                "नीचे के पत्र बताए गए बैंकों को भेजें। जवाब आने पर उनके स्टेटमेंट जोड़ें (स्टेप 1) और चित्र एक किस्त और बढ़ जाएगा।"),
    # ---- connections: network / timeline / hour / split
    "net_show": ("Each square is a complaint. Each circle is a bank account that received stolen money from two or more complaints, so complaints joined by the same circle belong to the same gang. "
                 "The numbered circles are the busiest accounts; they are explained below the picture.",
                 "हर चौकोर एक शिकायत है। हर गोला ऐसा बैंक खाता है जिसमें दो या ज़्यादा शिकायतों का चोरी का पैसा आया, यानी एक ही गोले से जुड़ी शिकायतें एक ही गिरोह की हैं। "
                 "नंबर वाले गोले सबसे व्यस्त खाते हैं; उनका ब्योरा चित्र के नीचे है।"),
    "net_line": ("**{n}. {acct}** ({bank}): used by {k} complaints · received ₹{total} · ₹{inside} still inside · suspicion {score}/100",
                 "**{n}. {acct}** ({bank}): {k} शिकायतों में इस्तेमाल · ₹{total} मिला · ₹{inside} अभी अंदर · संदेह {score}/100"),
    "net_line_exit": ("**{n}. {acct}**: cash-out point used by {k} complaints · ₹{total} taken out",
                      "**{n}. {acct}**: {k} शिकायतों में इस्तेमाल हुआ कैश-आउट बिंदु · ₹{total} निकाला गया"),
    "net_next": ("Start with number 1: freezing one account that many victims paid into helps all of them at once. Send each bank one combined request (tab 'Combined report & bank file').",
                 "नंबर 1 से शुरू करें: जिस खाते में कई पीड़ितों ने पैसा भेजा उसे फ्रीज़ कराने से सबको एक साथ फायदा होता है। हर बैंक को एक संयुक्त अनुरोध भेजें (टैब 'संयुक्त रिपोर्ट और बैंक फाइल')।"),
    "tl_show": ("Each row is a shared account; each dot is a moment when stolen money arrived in it. Dot colour = which complaint, bigger dot = more money. A ★ on the top row marks the moment each fraud started.",
                "हर पंक्ति एक साझा खाता है; हर बिंदु वह क्षण है जब उसमें चोरी का पैसा आया। बिंदु का रंग = कौन-सी शिकायत, बड़ा बिंदु = ज़्यादा पैसा। ऊपर की पंक्ति में ★ हर धोखाधड़ी की शुरुआत बताता है।"),
    "tl_next": ("If dots of different colours hit the same account within minutes, the gang is working several victims at once. Warn the banks for the same time of day, and watch these accounts for new activity.",
                "अगर अलग-अलग रंग के बिंदु एक ही खाते में कुछ मिनटों के भीतर आएँ, तो गिरोह एक साथ कई पीड़ितों पर काम कर रहा है। बैंकों को दिन के उसी समय के लिए सतर्क करें और इन खातों पर नई हलचल देखें।"),
    "hr_show": ("How many frauds started in each hour of the day. Dark bars are night (10pm–6am), orange bars are daytime.",
                "दिन के हर घंटे में कितनी धोखाधड़ी शुरू हुई। गहरी पट्टी रात (रात 10 से सुबह 6) है, नारंगी पट्टी दिन है।"),
    "hr_next": ("Plan for the busiest hours: keep a freeze contact at each major bank available at those times.", "सबसे व्यस्त घंटों की तैयारी रखें: उन समयों पर हर बड़े बैंक में फ्रीज़ के लिए संपर्क उपलब्ध रखें।"),
    "sp_show": ("When one account holds money from several complaints, this shows how much came from each complaint. Each bar is one shared account; each colour is one complaint.",
                "जब एक खाते में कई शिकायतों का पैसा हो, तो यह दिखाता है कि हर शिकायत से कितना आया। हर पट्टी एक साझा खाता है; हर रंग एक शिकायत।"),
    "sp_next": ("If money is recovered from a shared account, use this split as supporting evidence for sharing it between the victims. The final split is decided by the bank or court.",
                "अगर किसी साझा खाते से पैसा वापस मिले, तो पीड़ितों में बाँटने के लिए इस बँटवारे को सहायक सबूत की तरह इस्तेमाल करें। अंतिम बँटवारा बैंक या अदालत तय करती है।"),
    "how_group": ("How strong is this group? {s} strong and {p} probable links hold it together.", "यह समूह कितना पक्का है? {s} पक्के और {p} संभावित जुड़ाव इसे बाँधते हैं।"),
})


T.update({
    "br_headline": ("₹{amt} was stolen from account {acct}. It passed through {n} accounts in {s} steps.",
                    "खाता {acct} से ₹{amt} चोरी हुए। पैसा {s} कदमों में {n} खातों से गुज़रा।"),
    "br_headline_none": ("₹{amt} was stolen from account {acct}. No onward payments were found in the data yet.",
                         "खाता {acct} से ₹{amt} चोरी हुए। डेटा में अभी आगे का कोई भुगतान नहीं मिला।"),
    "br_freeze": ("Ask **{bank}** to freeze account **{acct}** NOW. About ₹{amt} of the stolen money is still inside.",
                  "**{bank}** से खाता **{acct}** अभी फ्रीज़ कराएँ। इसमें चोरी का लगभग ₹{amt} अभी अंदर है।"),
    "br_hold": ("Ask **{bank}** to hold / verify and send statements for: {accts}. They look like mule accounts (money only passed through them).",
                "**{bank}** से इन खातों को रोकने / जाँचने और स्टेटमेंट भेजने को कहें: {accts}। ये म्यूल खाते लगते हैं (पैसा बस इनसे होकर गुज़रा)।"),
    "br_cash": ("Money left the banks through: {names}. Ask these cash-out points for their records (CCTV, KYC, withdrawal details).",
                "पैसा बैंकों से यहाँ से बाहर गया: {names}। इन कैश-आउट बिंदुओं से रिकॉर्ड माँगें (CCTV, KYC, निकासी का ब्योरा)।"),
    "br_gang_check": ("Check whether other complaints involve the same gang accounts, then combine them into one case (tab 'Connections between complaints').",
                      "देखें कि क्या दूसरी शिकायतों में भी यही गिरोह के खाते हैं, फिर उन्हें एक केस में जोड़ें (टैब 'शिकायतों के बीच जुड़ाव')।"),
    "br_gang": ("These accounts look connected to a larger gang of {n} accounts (shared devices, phones or cash-out points). Other gang accounts to check against other complaints: {extra}.",
                "ये खाते {n} खातों के बड़े गिरोह से जुड़े लगते हैं (साझा डिवाइस, फोन या कैश-आउट बिंदु)। दूसरी शिकायतों से मिलाने के लिए गिरोह के और खाते: {extra}।"),
})


T.update({
    "view_list": ("📋 All complaints (search)", "📋 सभी शिकायतें (खोजें)"),
    "view_one": ("📁 One complaint file", "📁 एक शिकायत की फाइल"),
    "view_links": ("🔗 Connections between complaints", "🔗 शिकायतों के बीच जुड़ाव"),
    "list_title": ("All complaints", "सभी शिकायतें"),
    "list_help": ("Every row is one complaint. Type in the search box to find one, then click its row (or use the 'Open' button) to see its full analysis.",
                  "हर पंक्ति एक शिकायत है। खोज बॉक्स में टाइप करके शिकायत ढूँढें, फिर उसकी पंक्ति पर क्लिक करें (या 'खोलें' बटन दबाएँ) और पूरा विश्लेषण देखें।"),
    "search_lbl": ("Search", "खोजें"),
    "search_ph": ("Type a complaint no., victim name, phone, UPI id, account number (victim or mule), bank or case…",
                  "शिकायत नंबर, पीड़ित का नाम, फोन, UPI id, खाता नंबर (पीड़ित या म्यूल), बैंक या केस लिखें…"),
    "search_help": ("You can type just a part, e.g. the last 4 digits of an account or phone. Several words = all of them must match. Searching a mule account finds every complaint whose money passed through it.",
                    "सिर्फ़ हिस्सा लिखना काफ़ी है, जैसे खाते या फोन के आख़िरी 4 अंक। कई शब्द लिखें तो सब मिलने चाहिए। म्यूल खाता खोजने पर वे सभी शिकायतें मिलेंगी जिनका पैसा उससे गुज़रा।"),
    "flt_title": ("Filters (bank, date, amount, status)", "फ़िल्टर (बैंक, तारीख, रकम, स्थिति)"),
    "flt_bank": ("Bank on the money trail", "पैसे के रास्ते में बैंक"), "flt_date": ("Fraud date between", "धोखाधड़ी की तारीख"),
    "flt_amt": ("Amount lost (₹) between", "गई रकम (₹)"), "flt_status": ("Status", "स्थिति"), "flt_case": ("Only complaints that belong to a gang case", "सिर्फ़ वे शिकायतें जो किसी गिरोह-केस से जुड़ी हैं"),
    "ov_line": ("{n} complaints · {new} new · {frozen} money frozen · {cases} gang case(s)", "{n} शिकायतें · {new} नई · {frozen} में पैसा फ्रीज़ · {cases} गिरोह-केस"),
    "res_n": ("{k} of {n} complaints match", "{n} में से {k} शिकायतें मिलीं"),
    "res_none": ("No complaint matches. Clear the search or filters.", "कोई शिकायत नहीं मिली। खोज या फ़िल्टर हटाएँ।"),
    "open_pick": ("Selected complaint", "चुनी हुई शिकायत"), "open_btn": ("Open analysis →", "विश्लेषण खोलें →"),
    "click_hint": ("Tip: click a row in the table to select it, then press 'Open analysis'.", "सुझाव: तालिका की किसी पंक्ति पर क्लिक करके चुनें, फिर 'विश्लेषण खोलें' दबाएँ।"),
    "back_list": ("← Back to all complaints", "← सभी शिकायतों पर वापस"),
    "na": ("not in the file", "फाइल में नहीं है"),
    # table column names + their "?" help
    "cl_id": ("Complaint no.", "शिकायत नंबर"), "cl_victim": ("Victim", "पीड़ित"), "cl_phone": ("Phone", "फोन"),
    "cl_fraud": ("Fraud happened", "धोखाधड़ी कब हुई"), "cl_filed": ("Complaint filed", "शिकायत कब दर्ज हुई"), "cl_delay": ("Delay (hours)", "देरी (घंटे)"),
    "cl_amt": ("Lost (₹)", "गई रकम (₹)"), "cl_status": ("Status", "स्थिति"), "cl_case": ("Gang case", "गिरोह-केस"),
    "cl_inside": ("Still inside (₹)", "अभी अंदर (₹)"), "cl_cash": ("Cashed out (₹)", "निकाला जा चुका (₹)"), "cl_match": ("Matched on", "यहाँ मिला"),
    "ch_id": ("The number given by the cyber-crime portal (NCRP acknowledgement no.) for this complaint.", "साइबर-क्राइम पोर्टल (NCRP) द्वारा इस शिकायत को दिया गया पावती नंबर।"),
    "ch_fraud": ("When the victim's money actually left the account.", "जब पीड़ित का पैसा असल में खाते से गया।"),
    "ch_filed": ("When the victim reported it. The earlier, the more money can still be saved.", "जब पीड़ित ने शिकायत की। जितनी जल्दी, उतना ज़्यादा पैसा बच सकता है।"),
    "ch_delay": ("Hours between the fraud and the complaint. Up to 1 hour is the 'golden hour': money is usually still inside.", "धोखाधड़ी और शिकायत के बीच के घंटे। 1 घंटे तक 'गोल्डन ऑवर' है: पैसा अक्सर अभी अंदर होता है।"),
    "ch_inside": ("Stolen money still sitting in bank accounts. This can still be frozen.", "चोरी का पैसा जो अभी बैंक खातों में पड़ा है। इसे अब भी फ्रीज़ कराया जा सकता है।"),
    "ch_cash": ("Stolen money already taken out as ATM / wallet / crypto / cash. Hard to get back.", "चोरी का पैसा जो ATM / वॉलेट / क्रिप्टो / नकद में निकल चुका है। वापस पाना मुश्किल।"),
    "ch_case": ("Complaints joined into one gang case because their money passed through the same accounts. Blank = stands alone.", "वे शिकायतें जो एक गिरोह-केस में जुड़ी हैं क्योंकि उनका पैसा उन्हीं खातों से गुज़रा। खाली = अकेली।"),
    "ch_status": ("Where the investigation stands. You can change it on the complaint page; it is saved on this computer.", "जाँच कहाँ तक पहुँची। आप इसे शिकायत के पेज पर बदल सकते हैं; यह इसी कंप्यूटर पर सेव रहता है।"),
    "ch_victim": ("Name and phone come from the complaints file, if it had those columns.", "नाम और फोन शिकायत वाली फाइल से आते हैं, अगर उसमें ये कॉलम थे।"),
    "st_new": ("🆕 New", "🆕 नया"), "st_investigating": ("🔍 Investigation ongoing", "🔍 जाँच जारी"),
    "st_frozen": ("🧊 Money frozen", "🧊 पैसा फ्रीज़"), "st_closed": ("✅ Closed", "✅ बंद"),
    "note_lbl": ("Your note (optional)", "आपका नोट (वैकल्पिक)"), "note_saved": ("Saved on this computer", "इस कंप्यूटर पर सेव हुआ"),
    # complaint card
    "card_title": ("Complaint file", "शिकायत की फाइल"),
    "card_who": ("👤 Who complained", "👤 किसने शिकायत की"), "card_when": ("🕒 When", "🕒 कब"), "card_money": ("💰 How much", "💰 कितना पैसा"), "card_case": ("🔗 Gang case", "🔗 गिरोह-केस"),
    "who_name": ("Name", "नाम"), "who_phone": ("Phone", "फोन"), "who_acct": ("Victim account", "पीड़ित का खाता"), "who_upi": ("UPI id", "UPI id"),
    "when_fraud": ("Fraud", "धोखाधड़ी"), "when_filed": ("Complaint filed", "शिकायत"), "when_delay": ("Delay", "देरी"),
    "delay_val": ("{h:.1f} hours", "{h:.1f} घंटे"), "delay_unknown": ("filing time not in the file", "दर्ज होने का समय फाइल में नहीं"),
    "m_lost": ("Lost", "गई"), "m_inside": ("Still inside", "अभी अंदर"), "m_cash": ("Cashed out", "निकाल लिया गया"),
    "case_single": ("This complaint does not share accounts with any other complaint (so far).", "इस शिकायत के खाते किसी और शिकायत से साझा नहीं (अभी तक)।"),
    "case_with": ("Part of **{gid}** together with {n} other complaint(s):", "**{gid}** का हिस्सा, साथ में {n} और शिकायत(ें):"),
    "case_open": ("Open {cid}", "{cid} खोलें"),
    "banks_inv": ("Banks on the trail", "रास्ते के बैंक"), "first_call": ("Call first", "पहले फोन करें"),
    "first_call_v": ("{bank} → account {acct} (₹{amt} still inside)", "{bank} → खाता {acct} (₹{amt} अभी अंदर)"),
    "first_call_none": ("No account still holds stolen money; ask banks for statements and KYC.", "किसी खाते में अब चोरी का पैसा नहीं; बैंकों से स्टेटमेंट और KYC माँगें।"),
    "when_box": ("Look at the situation some minutes after the fraud (time travel)", "धोखाधड़ी के कुछ मिनट बाद की स्थिति देखें (समय में पीछे)"),
    "card_help": ("This card answers: who complained, when, how much was lost, where it stands now and which gang it is linked to. The picture and the action list below are for THIS complaint only.",
                  "यह कार्ड बताता है: किसने शिकायत की, कब, कितना गया, अभी स्थिति क्या है और कौन-से गिरोह से जुड़ी है। नीचे का चित्र और कार्रवाई की सूची सिर्फ़ इसी शिकायत की है।"),
    "gl_search": ("Search a word in the glossary", "शब्दकोश में कोई शब्द खोजें"),
    "gl_extra": (
        "\n- **Complaint no. / acknowledgement no.**: the number the cyber-crime portal gives each complaint.\n"
        "- **Gang case (CASE-1…)**: complaints joined together because their stolen money passed through the same accounts, cash-out points or devices.\n"
        "- **Status**: new · investigation ongoing · money frozen · closed. You set it yourself on the complaint page.\n"
        "- **Golden hour**: the first hour after the fraud. If the complaint arrives inside it, the money is usually still in the first accounts.\n"
        "- **Delay**: hours between the fraud and the complaint being filed.\n"
        "- **Still inside / Cashed out**: stolen money still sitting in accounts (can be frozen) / already taken out as cash, ATM, wallet or crypto.\n"
        "- **UPI id (VPA)**: a payment address like name@bank.",
        "\n- **शिकायत नंबर / पावती नंबर**: साइबर-क्राइम पोर्टल हर शिकायत को जो नंबर देता है।\n"
        "- **गिरोह-केस (CASE-1…)**: वे शिकायतें जो इसलिए जुड़ी हैं क्योंकि चोरी का पैसा उन्हीं खातों, कैश-आउट बिंदुओं या डिवाइसों से गुज़रा।\n"
        "- **स्थिति**: नया · जाँच जारी · पैसा फ्रीज़ · बंद। इसे आप खुद शिकायत के पेज पर तय करते हैं।\n"
        "- **गोल्डन ऑवर**: धोखाधड़ी के बाद का पहला घंटा। इसमें शिकायत आए तो पैसा अक्सर पहले खातों में ही होता है।\n"
        "- **देरी**: धोखाधड़ी और शिकायत दर्ज होने के बीच के घंटे।\n"
        "- **अभी अंदर / निकाला जा चुका**: चोरी का पैसा जो खातों में पड़ा है (फ्रीज़ हो सकता है) / जो नकद, ATM, वॉलेट या क्रिप्टो में निकल चुका।\n"
        "- **UPI id (VPA)**: भुगतान का पता, जैसे name@bank।"),
})
ROLE.update({"victim_name": ("Victim / complainant name", "पीड़ित / शिकायतकर्ता का नाम"), "victim_phone": ("Victim mobile number", "पीड़ित का मोबाइल नंबर"),
             "victim_upi": ("Victim UPI id", "पीड़ित की UPI id")})
