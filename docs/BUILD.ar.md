# تحويل المشروع إلى ISO

**حالة الإصدار:** الكود قابل للتطوير والاختبار، لكن لا يُسمّى ISO نهائيًا قبل اجتياز مصفوفة الإقلاع في `VALIDATION.md`. اقرأ `HANDOFF.md` للحالة الفعلية الأخيرة. لا تخلط بين نجاح اختبارات Python وبين إقلاع نظام تشغيل.

## جهاز البناء

- Linux x86_64، Docker يعمل أو Arch Linux أصلي. `mkarchiso` يحتاج root وmount؛ حاوية البناء تحتاج `--privileged`.
- يوصى 16GB RAM و100GB مساحة فارغة للنسخة الكاملة، ومعالج 4 أنوية. سكربت ضغط ISO يستخدم عاملين لحماية الذاكرة.
- الجهاز المستهدف 8GB RAM. هذا مختلف عن متطلبات تجميع كل الحزم والصور.
- تجنّب Docker driver `vfs` في بناء النسخة الكاملة؛ تكرار طبقات الصور قد يحتاج مساحة أكبر بكثير. استخدم Docker مع overlay2 على ext4.
- اتصال بمرايا Arch، GitHub، PyPI، Docker Hub، PortSwigger، وسجل Ollama. راجع نطاقات `NETWORK.md`.

## النسختان

| الاختيار | ما يتضمنه | أول تشغيل للخدمات |
|---|---|---|
| `full` | سطح المكتب، التطبيقات، صور الخدمات، نموذج Qwen 1.5B | بلا تنزيل إذا اكتمل التجميع والتحقق؛ يحتاج قرص بيانات للخدمات الثقيلة |
| `desktop` | سطح المكتب، التطبيقات، Studio وFlow وملفات الخدمات | الإنترنت مطلوب لتنزيل الصور والنموذج |

النسخة المطلوبة للمناقشة هي `full`. `desktop` مفيدة لاختبار الإقلاع سريعًا وليست بديلًا مكتملاً عن طلب النسخة دون إنترنت.

## البناء من Linux مع Docker

نفّذ من جذر checkout المشروع:

```bash
docker build -t 9b7-builder -f scripts/builder.Dockerfile .
docker run --rm --privileged -v "$PWD:/project" 9b7-builder bash scripts/build-extra-packages.sh
# يحتاج Docker وPython على المضيف؛ هذا يحفظ صور الخدمات والنموذج في cache/offline.
python3 scripts/bundle-offline.py
docker run --rm --privileged -v "$PWD:/project" 9b7-builder bash scripts/build-iso.sh full
```

النتيجة في `out/`: ISO، SHA256، قائمة حزم، ومرجع الكود. حزم Arch تُتحقق بتوقيعاتها؛ الحزم الإضافية بمراجع AUR مثبتة، checksums مصادر، وتوقيع مفتاح بناء محلي. المفتاح الخاص يبقى في `cache/signing` ولا يدخل Git أو ISO.

لبناء نسخة اختبار دون صور الخدمات:

```bash
docker run --rm --privileged -v "$PWD:/project" 9b7-builder bash scripts/build-iso.sh desktop
```

لا تشغّل `build-extra-packages.sh` على نظامك اليومي: يُنشئ مستخدم بناء وصلاحية pacman داخل بيئة البناء المخصصة. لا تحذف توقيعات أو تستخدم `--skippgpcheck` لعلاج فشل تنزيل.

في بيئة cloud ذات proxy بشهادة CA مُدارة، مرّر **الشهادة العامة الموثوقة التي توفرها المنصة** أثناء بناء الحاوية: `docker build --secret id=build_ca,src=/path/to/platform-ca.crt -t 9b7-builder -f scripts/builder.Dockerfile .`. لا تعطّل TLS. هذه الشهادة تخص أداة البناء ولا تُنسخ عمدًا إلى نظام اللاب النهائي.

## تشغيل البناء على GitHub

`Actions → Build ISO → Run workflow` يبني `desktop` على GitHub runner أو `full` على self-hosted runner مناسب. مسار full مقصود أن يعمل على جهازك المخصص ذو مساحة كافية. لا تضع أسرارًا في workflow. النتيجة artifact خاصة بتشغيل Actions؛ لا تنشر Release تلقائيًا قبل اختبار الإقلاع والتراخيص.

## VirtualBox

1. أنشئ جهاز Linux / Arch Linux 64-bit، ذاكرة 4096MB، معالجين، VMSVGA، ذاكرة فيديو 128MB، واترك 3D acceleration مغلقًا كبداية.
2. أنشئ قرص VDI ديناميكي 64GB على الأقل؛ 80GB أنسب للخدمات الكاملة.
3. اختر ملف ISO كقرص optical. UEFI وLegacy BIOS مدعومان في profile، وكلاهما يحتاج اختبارًا فعليًا قبل الإصدار.
4. اختر **Compatibility / XFCE**. شاشة الدخول: `9b7` / `9b7`.
5. استخدم **Install 9b7 Linux** لتثبيت نفس التخصيصات على الـVDI. بعد نجاح التثبيت أخرج الـISO وأعد التشغيل.
6. خصص 5–6GB للـVM إذا كنت ستعرض ERPNext، وأغلق البرامج الثقيلة على المضيف. لا تتوقع ERPNext وكل أدوات BI معًا على لاب 8GB.

## USB واللاب

- نفس ISO يصلح USB وVirtualBox. استخدم Ventoy أو Rufus بوضع DD؛ حرق ISO يمسح الفلاشة المحددة.
- عطّل Secure Boot لهذه النسخة؛ لا تتضمن سلسلة توقيع Secure Boot. لا تغيّر إعدادات firmware أخرى بلا داعٍ.
- اختر Live للتجربة أو Compatibility لو العرض الرسومي تعثّر. وجود NVIDIA قد يحتاج تعريفًا مناسبًا واختبارًا منفصلًا؛ لا ندّعي دعم كل كروت NVIDIA.
- جلسة Live مؤقتة. تشغيل Docker من ISO على جهاز 8GB يحتاج تخزين ext4 دائم للخدمات أو تثبيت النظام على القرص؛ مساحة RAM المؤقتة ليست مخزنًا مناسبًا لصور ERP.
- لو عندك قسم ext4 مركّب مسبقًا وبه 20GB+ فارغة: نفّذ `sudo 9b7-storage /path/to/mount` قبل تشغيل الخدمات. الأداة لا تفرمت؛ ترفض استبدال Docker store به بيانات. في كل جلسة Live جديدة أعد تركيب القسم وتفعيل المخزن نفسه. لا تعتمد على FAT32/exFAT كمخزن Docker.
- المثبت الحالي يمسح **قرصًا كاملاً** بعد كتابة `ERASE /dev/...`؛ ليس مثبت dual-boot. ابدأ باختباره على VDI فارغ، ولا تختبره على قرص عليه ملفاتك.

## خطوات قبول الإصدار

شغّل اختبارات الكود، ابن full، تحقق من SHA256، اختبر BIOS وUEFI وVirtualBox، اختبر الإقلاع الثاني بعد التثبيت، ثم افصل الإنترنت واختبر كل خدمة منفردة. سجّل النتائج في `VALIDATION.md`. عندها فقط أنشئ Release باسم الإصدار وارفع الـISO وSHA256 وقائمة الحزم وملاحظات التراخيص.
