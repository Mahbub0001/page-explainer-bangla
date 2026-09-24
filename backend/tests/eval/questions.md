# Evaluation Dataset: 10 Pages × 5 Questions

This evaluation set benchmarks the Bangla Page Explainer against PRD §10 criteria:
- Output in Bangla script and readable (target >= 90%)
- Factually supported by page context (target >= 85%)
- Trap questions (answer not on page) correctly produce the refusal behavior (target >= 80%)

---

### Page 1: Wikipedia - Solar System (Science Article)
- **Q1 (English):** What are the planets mentioned in this system?
- **Q2 (Bangla):** সৌরজগতের সবচেয়ে ছোট গ্রহ কোনটি?
- **Q3 (Banglish):** mangal grahe ki ache?
- **Q4 (Follow-up):** shukro graho keno gorom?
- **Q5 (Trap):** টাইটানিক জাহাজ কোন মহাসাগরে ডুবেছিল?

### Page 2: Mozilla MDN - JavaScript Promises (Technical Docs)
- **Q1 (English):** What are the three states of a Promise?
- **Q2 (Bangla):** প্রমিজ কীভাবে অ্যাসিনক্রোনাস কাজ পরিচালনা করে?
- **Q3 (Banglish):** promise er kaj ki?
- **Q4 (Bangla):** .then() এবং .catch() এর মধ্যে পার্থক্য কী?
- **Q5 (Trap):** পাইথন জ্যাঙ্গো কীভাবে ইনস্টল করতে হয়?

### Page 3: BBC News - Climate Change Summit (News Article)
- **Q1 (Bangla):** এই সম্মেলনে প্রধান আলোচ্য বিষয় কী ছিল?
- **Q2 (English):** What is the target temperature limit agreed upon?
- **Q3 (Banglish):** kon kon desh ei chuktite shohomot hoyeche?
- **Q4 (Bangla):** কার্বন নিঃসরণ কমাতে কী কী পদক্ষেপের কথা বলা হয়েছে?
- **Q5 (Trap):** বিশ্বকাপ ফুটবল ২০২৬ কোথায় অনুষ্ঠিত হবে?

### Page 4: Bangla Tech Blog - কৃত্রিম বুদ্ধিমত্তা ও ভবিষ্যৎ (Bangla Native Page)
- **Q1 (Bangla):** এই লেখায় এআই এর কোন দিক নিয়ে কথা বলা হয়েছে?
- **Q2 (Banglish):** AI kivabe shadharon manusher kaj shohoj korche?
- **Q3 (English):** Does the author discuss risks of artificial intelligence?
- **Q4 (Bangla):** ভবিষ্যৎ কর্মসংস্থান নিয়ে লেখকের মতামত কী?
- **Q5 (Trap):** চাঁদে পানির সন্ধান প্রথম কে পেয়েছিল?

### Page 5: Python Official Docs - Python Decorators (Technical Docs)
- **Q1 (English):** How does a decorator wrap a function?
- **Q2 (Bangla):** পাইথনে @ প্রতীক কী নির্দেশ করে?
- **Q3 (Banglish):** decorator keno bebohar kora hoy?
- **Q4 (Bangla):** functools.wraps কেন ব্যবহার করা ভালো?
- **Q5 (Trap):** সি++ এ পয়েন্টার কীভাবে ডিক্লেয়ার করে?

### Page 6: Healthline - Benefits of Regular Exercise (Health Article)
- **Q1 (Bangla):** প্রতিদিন ব্যায়াম করার প্রধান উপকারিতা কী?
- **Q2 (English):** How does physical activity affect cardiovascular health?
- **Q3 (Banglish):** ghumer shathe bayamer kono shomporko ache ki?
- **Q4 (Bangla):** মানসিক স্বাস্থ্যের উপর এর প্রভাব কী?
- **Q5 (Trap):** করোনাভাইরাস প্রথম কোন সালে শনাক্ত হয়েছিল?

### Page 7: Wikipedia - History of Dhaka (History Article)
- **Q1 (Bangla):** ঢাকা কখন সুবাহ বাংলার রাজধানী হয়েছিল?
- **Q2 (English):** Who was the Mughal subahdar who founded the capital in Dhaka?
- **Q3 (Banglish):** dhakar puraton nam ki chilo?
- **Q4 (Bangla):** লালবাগ কেল্লা কে নির্মাণ শুরু করেছিলেন?
- **Q5 (Trap):** আইফেল টাওয়ারের উচ্চতা কত মিটার?

### Page 8: Tutorialspoint - CSS Flexbox Guide (Tutorial)
- **Q1 (English):** What does justify-content do along the main axis?
- **Q2 (Bangla):** flex-direction: column দিলে আইটেমগুলো কীভাবে সাজবে?
- **Q3 (Banglish):** align-items diye ki kora jay?
- **Q4 (Bangla):** flex-wrap এর কাজ কী?
- **Q5 (Trap):** মাইএসকিউএল ডাটাবেজে টেবিল ড্রপ করার সিনট্যাক্স কী?

### Page 9: TechCrunch - Electric Vehicles Growth (Business / Tech)
- **Q1 (English):** What caused the surge in EV battery production?
- **Q2 (Bangla):** চার্জিং অবকাঠামো তৈরিতে প্রধান বাধাগুলো কী কী?
- **Q3 (Banglish):** kon company shobcheye beshi gari bikri koreche?
- **Q4 (Bangla):** সরকারি প্রণোদনা কীভাবে গ্রাহকদের উৎসাহিত করছে?
- **Q5 (Trap):** মঙ্গল গ্রহে মানুষের প্রথম বসতি কবে স্থাপন হবে?

### Page 10: Wikipedia - James Webb Space Telescope (Space Science)
- **Q1 (Bangla):** জেমস ওয়েব টেলিস্কোপের মূল আয়নাটি কী দিয়ে তৈরি?
- **Q2 (English):** What Lagrange point does the telescope orbit?
- **Q3 (Banglish):** eta kon roket diye uthkhepon kora hoyechilo?
- **Q4 (Bangla):** হাবল টেলিস্কোপের সাথে এর প্রধান পার্থক্য কী?
- **Q5 (Trap):** অলিম্পিকে সবচেয়ে বেশি স্বর্ণপদক কার দখলে?
