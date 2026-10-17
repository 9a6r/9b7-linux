# 9b7 Linux — سجل التنفيذ والتسليم

هذا الملف نقطة البداية لأي أداة أو مطور يكمل المشروع. حدّثه مع كل مرحلة، ولا تصف اختباراً بأنه ناجح ما لم يُنفّذ فعلاً.

## الهدف المتفق عليه

توزيعة Arch x86_64 لمشروع تخرج BIS، تقلع من USB وVirtualBox؛ Hyprland مع جلسة توافق XFCE؛ المستخدم وكلمة المرور الافتراضيان `9b7`. تطبيقنا **9b7 BIS Studio** وأداة أتمتتنا **9b7 Flow** يربطان تحليل بيانات الأعمال، قواعد البيانات، الأتمتة، ووكلاء AI محليين. Firefox، VSCodium، Docker، Odoo، Obsidian، Wireshark، Burp Suite Community، n8n، Superset، Metabase، Ansible، btop، ERPNext ضمن نطاق العمل.

## 2026-10-16 — المرحلة 0

- استُكمل إعداد الريبو من commit `ab66097` الموجود على GitHub؛ لم يُحذف أي عمل سابق.
- البيئة الحالية Debian 13، x86_64، نحو 30GiB مساحة كتابة و33GiB RAM؛ Docker يعمل.
- اختُبرت صلاحية mount داخل حاوية Docker مخصصة بنجاح؛ لا يوجد `/dev/kvm` في بيئة الوكيل.
- قرأنا profile releng الرسمي لـarchiso وملف ERPNext الرسمي `frappe_docker/pwd.yml`.
- مسار البناء: profile مشتق من releng؛ لا نعيد توزيع أكواد مغلقة بلا توثيق تراخيصها. لا ندّعي أن Omarchy أو Arch يدعم المشروع رسمياً.
- مطلوب اختبار فعلي للإقلاع BIOS/UEFI ثم VirtualBox/لابتوب قبل تسمية ISO إصداراً نهائياً.

## الحالة الحالية

أُنتج ISO كامل 11.5GiB واجتاز BIOS وUEFI في QEMU TCG. التثبيت والنشر لم يكتمل تحققهما بعد؛ انظر آخر مرحلة أدناه. اللاب 8GB RAM؛ لا تُشغّل الخدمات الثقيلة مجتمعة.

## قواعد إكمال العمل

1. اقرأ هذا الملف وREADME قبل أي تعديل، ثم `git status`.
2. استخدم checkout الموجود؛ لا تنشئ worktree دون طلب المستخدم.
3. شغّل الاختبارات، وسجّل النتيجة الفعلية والعوائق هنا.
4. اعمل commits صغيرة واضحة ثم push إلى الريبو؛ المستخدم طلب رفع العمل خطوة بخطوة.
5. لا تضع مفاتيح API أو أسرار حقيقية في Git. `9b7` بيانات دخول معملية طلبها المستخدم.
6. لا تشغّل خدمات ERP والتحليل كلها تلقائياً؛ ابدأ ما يحتاجه العرض من Studio.
7. لا تفرمت قرصاً أثناء التطوير. التثبيت النهائي يحتاج اختيار القرص وتأكيد المستخدم داخل المثبت.

## 2026-10-16 — المرحلة 1

- نُفّذ 9b7 Flow: CSV، تحقق، استيراد transactional إلى SQLite، منع التكرار، كشف تعارض IDs، تقارير HTML/JSON، وسجل أخطاء وتشغيل.
- نُفّذ 9b7 BIS Studio بواجهة Qt، استيراد وتقارير، إدارة الخدمات، ستة أنواع قواعد بيانات، وثلاثة وكلاء AI.
- 13 اختباراً آلياً نجح؛ اختُبرت الواجهة offscreen باستيراد حقيقي وقراءة SQLite؛ screenshot في `/tmp/9b7-studio.png`.
- جميع ملفات Compose السبعة اجتازت التحقق. تشغيل الخدمات الفعلي مستمر؛ لا تعتبرها متحققة بعد.
- تنزيل حزم Arch محجوب حالياً (proxy CONNECT 403 للمرايا). حُفظت نطاقات الشبكة المطلوبة في إعدادات البيئة وطلبنا من المستخدم حفظها/نشرها.
- هيكل Live desktop موجود؛ profile builder والمثبت ما زالا قيد التنفيذ.

## 2026-10-16 — المرحلة 2

- أُضيف مولد profile releng، Hyprland/XFCE، قوائم BIOS وUEFI، Plymouth، المستخدم 9b7، ومثبت whole-disk بتأكيد كتابي وفحوص تمنع لمس القرص المستخدم حالياً. المثبت لم يُشغّل على قرص حقيقي بعد.
- أُضيف توقيع حزم AUR المحلية؛ المراجع مثبتة في `packaging/aur-lock.json`، وتثبيت hashes صور الخدمات قيد التنفيذ.
- n8n 2.43.6: اجتاز HTTP health، استيراد وتشغيل `automation/n8n-demo.json` عبر CLI باستخدام `--id=9b7BISDemo0000001` و`N8N_RUNNERS_BROKER_PORT=5680`؛ status=success وfinished=true.
- Metabase 0.64.1: health=ok واستعلام فعلي على Sample Database أعاد 18760 صف orders. احتاج تهيئة أولى أطول؛ زيدت مهلة الجاهزية إلى 600 ثانية.
- حساب Metabase الذي أُنشئ للاختبار فقط لا يدخل ISO. أُزيلت حاويات/صور الاختبار بعد انتهائها لاستعادة المساحة.
- Docker في السحابة يستخدم vfs؛ محاولة سحب Superset أُوقفت قبل امتلاء المساحة. يجري إعادة الاختبار بعد تنظيف صورنا فقط.
- أُضيفت أتمتة inbox عبر systemd user path وAnsible playbook.

## 2026-10-16 — المرحلة 3

- Superset 6.1.0: تهيئة، دخول 9b7/9b7 وAPI `/api/v1/me/` نجحت؛ إيقاف وإعادة تشغيل نجحا دون إعادة إنشاء الحساب.
- الاختبارات أصبحت 15، تشمل Inbox فعلياً ورفض archive معدل قبل docker load.
- ثُبتت 10 صور Docker بـlinux/amd64 digests. أُصلح مسار offline باستخدام local tags + image ID لأن docker save/load لا يحتفظ بـRepoDigests.
- جُرّب توليد profile مقابل releng الرسمي في work/profile-validation؛ استُخدم Qt SVG renderer بدلاً من librsvg غير الموجود بالمضيف. هذا تحقق هيكلي فقط، وليس build أو boot.
- أُضيفت وثائق عربية، GitHub Actions، دليل BIS، تراخيص، storage helper لقسم ext4 دون فرمتة، وlock لحزم Python.
- تحديث الشبكة: فحص HTTPS جديد لمرايا Arch نجح (200)؛ manifest نموذج Ollama نجح. استُؤنف تجهيز Arch builder؛ لا تعتبر الشبكة محجوبة حالياً.

## 2026-10-16 — المرحلة 4 (بعد طلب «كمل وركز»)

- Odoo: كان ملف public config بصلاحية 0600 لا يقرأه uid داخل الحاوية؛ صُححت الصلاحيات، وأضيف التطبيع إلى setup-dev. أُنشئت قاعدة 9b7_validation فعلياً وتم الدخول بـ9b7 بنجاح.
- Arch builder: الحظر الشبكي انتهى، لكن الحاوية احتاجت شهادة CA العامة التي توفرها المنصة. أُضيفت للـtrust store دون تعطيل TLS، ونجح تثبيت archiso وQEMU وأدوات البناء. Dockerfile يدعم شهادة البناء عبر build secret اختياري.
- تحققت جميع أسماء حزم iso/packages.x86_64 من قواعد pacman الفعلية: لا حزم مفقودة.
- PostgreSQL وRedis وCassandra: خدمات فعلية healthy؛ محولات التطبيق نفذت queries. تحقق KPI الإيراد 39100 عبر PostgreSQL وRedis. أُزيلت بيانات الاختبار الخاصة بنا بعد الانتهاء.
- الحزم الإضافية: geomet بُني وتوقّع؛ Cassandra driver كشف dependency tomli فأُضيفت. أُصلح تهيئة pacman-key ومرور proxy عبر sudo داخل حاوية البناء. البناء مستمر.
- حُفظت install_script وstart_skill في مسودة البيئة؛ الإعداد الجديد قابل لإعادة التنفيذ عبر scripts/setup-dev.sh. نشر البيئة منفصل ولم يُدّع إنجازه.
- ERPNext قيد الاختبار. لا يوجد ISO بعد.

## 2026-10-16 — المرحلة 5

- اكتمل بناء وتوقيع VSCodium وObsidian وBurp Suite وgeomet وCassandra driver. أُصلحت اعتماديات Cassandra ونجح import فعلي في Arch/Python 3.14 للحزمة 3.30.1-2.
- نجح توليد profile أصلي كامل إلى work/profile-native-check-2 بعد معالجة git safe.directory للأوامر داخل الحاوية فقط.
- اختبار offline roundtrip فعلي نجح: docker save مضغوط، إزالة local tag، تحقق checksum، docker load ثم تشغيل مع --pull never.
- ثُبت manifest الرسمي لـQwen 1.5B وتحققت كل blob ببصمتها وحجمها؛ archive النموذج جاهز. الاستدلال الفعلي ما زال غير مختبر.
- تجميع صور الخدمات المضغوطة جارٍ داخل Docker مخصص overlay2 على tmpfs؛ تصدير كل صورة ثم إزالتها يحدّ الاستهلاك. Docker الخارجي vfs غير مناسب للمساحة المتاحة.
- سحب ERPNext نجح داخل Docker المتداخل لكن التشغيل اصطدم بـcgroup v2 domain threaded الخاص بالسحابة؛ لا تسجل نجاح ERPNext قبل تشغيله فعليًا داخل VM.
- أُضيف مسار بناء محدود القرص بقرص عمل منفصل NINEB7_WORK_DIR وNINEB7_BIND_OFFLINE=1، مع فحص المساحة وفصل مخرجات ISO. لم يُختبر build بعد. المسار الافتراضي ذو 100GB ما زال الموصى به.
- الاختبارات الـ15، ShellCheck، تكوين الخدمات السبعة واختبار archive المضغوط ناجحة.
- الخطوة التالية: إكمال scripts/bundle-offline.py --remove-exported والتحقق من الحزمة، ثم scripts/build-iso.sh full في Arch builder؛ سجل الإقلاع قبل أي ادعاء بجهوزية ISO.

- مراجعة قبل البناء: صُحح DEFAULT في قائمة BIOS من arch إلى 9b7، وأُزيل تكرار خيار إقلاع القرص، وأُضيفت خلفية وعنوان 9b7. حساب مساحة التثبيت يستخدم الحجم المنطقي للملفات حتى لا يقلل SquashFS المضغوط تقدير مساحة القرص.

## 2026-10-16 — المرحلة 6: نسخة VirtualBox مطلوبة بأسرع وقت

- طلب المستخدم تجربة ISO الآن ورفع كل العمل إلى GitHub؛ لا يطلب منه بناءها ما دام يمكننا إكمال البناء السحابي.
- اكتملت حزمة full: 10 صور Docker مضغوطة + Qwen، نحو 7.9GiB؛ verify-offline نجح.
- Ollama 0.40.5 الأصلي في حاوية Arch شغّل الوكلاء الثلاثة على التقرير التجريبي، وردت KPIs صحيحة. النموذج الصغير استنتج عملة غير معطاة؛ ضُيق prompt ويجب اعتبار المخرجات اقتراحات تحتاج مراجعة، كما تنص الواجهة. لم يُختبر Ollama داخل ISO بعد.
- فحص Qt النهائي نجح؛ screenshot حقيقية محفوظة في docs/images/studio.png.
- حزم desktop جرى تنزيلها والتحقق منها مسبقًا. البناء الكامل سيستخدم /tmp/9b7-iso-work داخل 9b7-builder، مع NINEB7_BIND_OFFLINE=1. cache pacman انتقل إلى tmpfs منفصل لتوفير القرص.
- المصادر مرفوعة تدريجيًا. ملف ISO لم يتولد بعد؛ يجب تسجيل نتيجته وإقلاعه قبل تسليم رابط تنزيل.

## 2026-10-16 — المرحلة 7: البناء الفعلي

- بدأ full من 3fa935d، في حاوية 9b7-builder ومسار /tmp/9b7-iso-work/iso-full.WkF1GR. كل حزم Arch ثُبتت؛ الحجم المنطقي للبرامج نحو 7.5GiB بالإضافة إلى 7.9GiB offline.
- cache pacman بحجم 3GiB امتلأ، فرُفع إلى 4GiB. نسخة Burp الجزئية رُفضت بالـchecksum؛ الأصل ومطابقة توقيعه وفهرسه صحيحان، وأُعيدت نسخته. لا تعطيل للتحقق.
- kernel hook فشل بسبب غياب /dev/stdin في devtmpfs الخاص بالسحابة. arch-chroot -N يجهز روابط أجهزة خاصة ويعالج السبب؛ أُضيف استدراك محدود لهذه الحالة في build-iso.sh. توليد initramfs مستمر، ثم تستأنف mkarchiso من نفس work directory.
- سجلات مؤقتة: /tmp/9b7-iso-resume2.log و/tmp/9b7-initramfs-repair.log. لا تعد ISO جاهزًا قبل اكتمال الملف واختباره.

- توليد initramfs نجح بوضع namespace؛ إعداد BIOS وUEFI نجح. Studio اجتاز GUI smoke داخل root الفعلي بحزم Arch؛ Hyprland --verify-config أعاد config ok تحت مستخدم غير root. حُددت ذاكرة SquashFS بـ512MiB لأن الافتراضي الكبير غير مناسب لمسار tmpfs، وجارٍ ضغط ISO.


## 2026-10-17 — المرحلة 8: ISO موجود واختبار الإقلاع الفعلي

- الأصل محفوظ: `out/9b7-linux-2026.10.16-x86_64-full.iso`، الحجم الدقيق 12,352,876,544 بايت، مصدر البناء `8e538d7130751eeec62af0ca893ed3530bfbec89`.
- SHA-256: `b84e6627fea5ad1c063930321f7df8d9e7a6e9a75a30378a79113f02a5a43bc3`. أُعيد حسابه مرتين في جلسة 17 أكتوبر وطابق الملف المحفوظ؛ التحضير يحسب بصمة كل جزء أيضًا.
- QEMU TCG بلا KVM، 4096MiB و2 vCPU: UEFI وBIOS وصلا إلى LightDM. دخول 9b7/9b7 نجح. UEFI شغّل Hyprland وStudio فعليًا؛ صورتا الدليل في `docs/images/live-*.png`.
- Flow داخل ISO المقلع: 8 orders، revenue=39100، profit=22100؛ إعادة الاستيراد inserted=0 / duplicates=8. استخدام RAM نحو780MiB قبل الخدمات.
- يوجد تحذير systemd-loop عند محاولة تفسير أقسام CD-ROM؛ لا يمنع mount أو إقلاع Live. ليس ادعاء بأن كل وحدات systemd ناجحة. VirtualBox واللابتوب لم يُختبرا.
- بدأ اختبار تثبيت إلى QCOW2 جديد فارغ80GiB فقط في `/tmp/9b7-install-test/disposable.qcow2` داخل builder؛ لا أقراص مضيف مرفقة. سجل النتيجة قبل اعتماد المثبت.
- أُنشئت مسودة prerelease `v0.1.0-rc1`، release ID415499028. جميع محاولات رفع المرفقات، حتى41بايت، أعادت401 Bad credentials من uploads.github.com؛ API العادي وgit push يعملان. طلبنا تحديث ربط GitHub أو GH_TOKEN عبر إعدادات الأسرار، لا داخل المحادثة. **لا مرفقات منشورة حتى الآن.**
- `scripts/release-iso.py`: prepare يحسب7أجزاء1900MiB دون نسخ ISO؛ upload يحاول مرفقًا صغيرًا أولًا ويستأنف اعتمادًا على digest للخادم؛ verify ينزّل الأجزاء المنشورة دون توثيق ويقارن SHA الكلي والأجزاء. helpers Linux/Windows وmanifest جاهزة في work/release-delivery.
- 19اختبارًا +ShellCheck وتكوين الخدمات السبعة نجحوا؛ اختبارات إضافية للتجميع الفعلي ورفض الجزء الناقص/المعدل وعدم الكتابة فوق ISO سابق. PowerShell على Windows لم يُنفذ هنا.
- الأمر التالي للرفع بعد إصلاح التوثيق: `python3 scripts/release-iso.py upload --iso out/9b7-linux-2026.10.16-x86_64-full.iso`، ثم تحديث ملاحظات الإصدار، نشره كـprerelease، ثم `python3 scripts/release-iso.py verify` قبل إعلان توفر تنزيل متحقق منه.
