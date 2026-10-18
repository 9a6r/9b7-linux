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


## 2026-10-17 — المرحلة 9: تصحيح التوافق ثم طلب الثيمات الأصلية

**أولوية المستخدم الجديدة:** استخدام `SDDM.zip` الأصلي (ZIP يحتوي TAR باسم SDDM، ثم Slot-SDDM-6/QML/Qt6) و`plymouth theme.zip` الأصلي (arch-slider-and-glow). اختبار SDDM مع Hyprland/XFCE وخطة LightDM احتياطية؛ اختبار الأنيميشن وتسجيل الدخول في BIOS/UEFI مع صور، ثم **Desktop ISO أولًا؛ لا تعِد بناء Full قبل نجاح Desktop**.

- بحثنا عن الأرشيفين في /workspace و/tmp ومساحات الملفات المشتركة والحاوية وتاريخ Git ومرفقات Release. لا توجد نسخة منهما أو معرف تنزيل مرفق في السياق الحالي. لا تستبدلهما بثيم من الإنترنت ولا تدّع دمجهما. المطلوب إعادة إرفاق الأرشيفين؛ لم نثبت SDDM أو نبدّل مدير الدخول قبل فحصهما.
- عيب فعلي في LightDM: lightdm.conf الرئيسي يُقرأ بعد conf.d، فكان user-session=9b7-hyprland يُبطل 90-9b7-compat.conf. نُقل الافتراضي إلى 50-9b7-default.conf؛ parser الحقيقي أكد XFCE مع override وHyprland بدونه. أصلح wrapper الخاص بـHyprland لاستخدام D-Bus الخاص بـsystemd user عند وجوده، بدل إنشاء bus منفصل يكسر تفعيل بعض الخدمات.
- اختبارات Python الـ19، ShellCheck وتكوين الخدمات السبعة نجحت بعد الإصلاح. التجميع ورفض الملفات المعدلة/المخرجات الموجودة نجحت أيضًا عبر PowerShell7 الحقيقي على Linux؛ Windows نفسه غير مختبر.
- قدم المستخدم اعتماد رفع مؤقتًا؛ نجح رفع metadata والأجزاء01–04 من الأصل إلى **المسودة فقط**. أُوقف رفع الأصل بعد اكتشاف عيب التوافق. لم تُنشر Release مكتملة، ولا يجوز عرض المسودة كتنزيل صالح للتجميع؛ ينقصها03أجزاء. لا تحفظ التوكن في ملفات أو Git.
- scripts/release-iso.py أصبح يدعم streaming لجزأين متوازيين دون نسخة مؤقتة1.9GiB، ويتحقق من digest الخادم. أُطلق اختبار رفع stream صغير، لكن مخرجه لم يُحفظ قبل تغير جلسة الأدوات؛ يلزم إعادة تحقق الرفع المتدفق قبل الاعتماد عليه. إعادة تنزيل النسخة الكبيرة كاملة لم تُنفذ.
- الـISO الأصلي في out لم يتغير ولم يُحذف. لم يبدأ إعادة ضغط Full المصحح قبل وصول توجيه Desktop. ملف out/ORIGINAL-SOURCE-COMMIT يحفظ مرجع الأصل.

### حالة الموارد عند الاستكمال

- Arch builder: 9b7-builder. Native root: /tmp/9b7-iso-work/iso-full.WkF1GR/work/x86_64/airootfs (حوالي9GiB دون cache المكرر)؛ تصحيحات LightDM وwrapper مطبقة فيه فقط، لا في ISO الأصلي.
- الأرشيفات offline محفوظة داخل ISO الأصلي. طابقت byte-for-byte الكاش قبل إزالة النسخة المكررة لتوفير القرص. squashfuse يركب ISO عند offset269162496 في /tmp/9b7-original-root؛ منه bind إلى /project/cache/offline وإلى native root/opt/9b7/offline. هذه mounts داخل الحاوية؛ المضيف يرى مجلد cache/offline فارغًا. إذا فقدت mounts أعد تركيب الأصل؛ لا تدّع ضياع محتوى الحزمة.
- حزم AUR الموقعة محفوظة على المضيف في /tmp/9b7-preserved-packages؛ cache/packages symlink إليها. هذا المسار غير موجود داخل الحاوية الحالية؛ أعد إتاحته للحاوية إذا احتجت pacman المحلي. مفاتيح التوقيع محفوظة ولم تدخل Git.
- اختبار التثبيت: QEMU TCG4GiB/2CPU، SSH2231 داخل builder، QMP /project/work/install-qmp.sock، القرص الفارغ80GiB في /tmp/9b7-install-test/disposable.qcow2. المثبت الحقيقي بدأ التقسيم والنسخ ثم أُوقف rsync بـSIGSTOP مؤقتًا لتوفير RAM أثناء تجهيز الإصلاح (PIDs1496,1499,1506 داخل الضيف، تحقق منها قبل استخدامها). النسخ **غير مكتمل**، ولا يوجد إقلاع قرص مثبت ناجح.
- guest source هو ISO الأصلي؛ config LightDM وwrapper صُححا في Live، وconfig LightDM في target /mnt/9b7-install.pvzFqF. لا تخلط هذا الاختبار مع اعتماد ISO جديد. عند متابعة النسخ: ثبت تغيرات wrapper في target بعد rsync أيضًا، أو أعد اختبار تثبيت Desktop الجديد من البداية.
- حصل التوقف مع بعض العمليات محفوظة عبر الحاوية؛ تحقق من حالتها. لا تفترض استمرار tool session IDs عبر الرسائل. يجب تحديث SOURCE-COMMIT ونسخ ملفات المشروع إلى root عند بناء أي ISO مصحح.

- فحص لاحق في الضيف المعاد استخدامه: parser يعرض XFCE لكن تسجيل الدخول أعاد جلسة Hyprland السابقة؛ يلزم فحص تفضيل الجلسة المخزن/اختيار XFCE صراحة أو الإقلاع من Desktop جديد. لا تسجل نجاح دخول XFCE بعد. Hyprland يعمل بالـwrapper المعدل.

## 2026-10-17 — المرحلة 10: DEsk والثيمان الأصليان

- وصل الأرشيفان مجددًا وفُكّا آمنًا؛ SDDM/SDDM هو TAR يحتوي Slot-SDDM-6. ملفات QML والرسوم أصلية؛ Plymouth arch-slider-and-glow الأصلي مدمج بترخيص MIT. لم يُنفذ أي install.sh خارجي. تفاصيل التراخيص والبصمات في docs/DESK-INTEGRATION.md وpackaging/*original-sha256.json.
- DEsk v0.1.2/195435a (MIT) آخر إصدار لكنه **Beta وليس مستقرًا**. بُني على Arch مع wlroots0.18.3 خاص تحت /opt/9b7/desk-wlroots، دون إزالة Hyprland. حزمة موقعة 2.4MiB، اختبار Meson words 1/1 ناجح. تشغيل الجلسة الفعلي لم يُختبر بعد.
- أضيف SDDM/Qt6 والثيم الأصلي، جلسة DEsk افتراضية وDEsk2D وXFCE احتياطي، وخيار رجوع LightDM من TTY. Plymouth يُختار قبل توليد initramfs. إعدادات/اختصارات DEsk الأصلية محفوظة، لوحة us/ara وAlt+Shift. واجهة DEsk العربية الكاملة غير متاحة upstream، وCairo يحتاج shaping/bidi؛ لا ندعي ترجمة مكتملة.
- أضيف 9b7 Control Center مستقل يعيد استخدام وظائف Studio للخدمات/قواعد البيانات/الوكلاء/Flow، مع حالة النظام وأدوات الشبكة والصوت. بقي Studio مستقلًا. launchers وأيقونات ومكتبة DEsk أضيفت.
- اختبار Qt كشف انهيارًا فعليًا في callbacks غير المرتبطة بـQObject في Studio.task؛ صُحح بتسليم النتائج إلى كائن على GUI thread. اختبار فعلي offscreen بعد الإصلاح نجح: حالة النظام، Flow بإيراد39100 وSQLite count8. اختبار المصدر19 وShellCheck/Compose7 نجح قبل آخر إصلاح وسيعاد قبل commit.
- الأصل Full ISO محفوظ دون تعديل. أُغلقت VM اختبار التثبيت القديم لتوفير الذاكرة؛ QCOW2 الجزئي محفوظ ولم يكتمل تثبيته. cache/packages عاد مجلدًا داخل المشروع بدلاً من symlink /tmp ليراه builder.
- الخطوة التالية: إنهاء تحديث native root بـSDDM/DEsk، توليد Desktop profile جديد مع إعادة استخدام الحزم المثبتة دون offline mount، إعادة initramfs ثم بناء Desktop وإقلاعه QEMU BIOS/UEFI. لم تُبن نسخة Desktop الجديدة بعد.

- ec40636 مرفوع: native Desktop build في /tmp/9b7-iso-work/iso-desktop.0db3QJ، سجل work/desktop-build.log. إصلاح initramfs المدمج عالج غياب /dev/stdin؛ الضغط بدأ. أول ISO يحمل ec40636 لا يصلح للنشر النهائي قبل تصحيح صيغة drawer التي كشفها فحص parser (app/thing/panel)، وأسماء DBeaver/Obsidian الفعلية. سيستخدم أولًا لاختبارات الإقلاع، ثم يعاد ضغط Desktop فقط بعد الإصلاحات.
- اختبارات GUI لكلا Studio وControl Center نجحت فعليًا. مسودة start_skill حُدّثت بالمسار الجديد واختبار Qt وشرط Desktop أولًا. اختبار صلاحية رفع مصغر بالاعتماد الافتراضي ما زال401؛ لم يعدل المسودة القديمة.
- أثناء أول ضغط Desktop أُوقف mksquashfs قبل إنشاء ISO لتقليل وقت الاختبارات: Desktop يستخدم zstd6 بدل15، وFull يبقى15. لا ISO تجريبي سابق حُذف؛ الأصل Full محفوظ. سيُدمج تصحيح drawer ومساعدة Studio في native root قبل استئناف الضغط، ويسجل SOURCE-COMMIT الجديد.

## 2026-10-17 — المرحلة 11: Desktop أولي وخارطة تطوير جديدة

- Desktop الأولي اكتمل من b009c38: out/9b7-linux-2026.10.17-x86_64-desktop.iso، 4,038,098,944 بايت؛ SHA256=70d4a3cf43fceb1f320b705a68b7282ac94bcb5c960492626d9a0b4fccc562d3. package list وSOURCE-COMMIT محفوظة. الأصل Full12,352,876,544بايت لم يتغير. Native Desktop root: /tmp/9b7-iso-work/iso-desktop.0db3QJ/work/x86_64/airootfs في builder.
- initramfs فُحص بـlsinitcpio فعليًا: theme config وtwo-step.so وanimation00/93 موجودة. لم ينشر Desktop بعد.
- QEMU11.1.2 انهار مع virtio-vga (kernel سجل segfault، لاOOM). إعادة UEFI بـstd VGA/4GiB/2CPU TCG تعمل: Plymouth الأصلي ظهر وتقدّم الشريط بصور حقيقية work/desk-uefi-frames/046.png وغيرها. الإقلاع حاليًا يؤخر plymouth-quit وquit-wait؛ لم يصل SDDM بعد، ولا ادعاء بنجاح الجلسة. QEMU PID107554، QMP work/desk-uefi-qmp.sock، SSH2232 لم يُفعّل بعد. capture-boot.py يحتجز QMP باتصال واحد، أوقف قبل استخدام qmp.py؛ الصور89إطارًا محفوظة.
- المستخدم أرسل خارطة موسعة docs/USER-ROADMAP-2026-10-17.md: الاسم الرسمي **9b7** فقط، الاحتفاظ الدائم بـDEsk/Hyprland/XFCE، Studio مؤسسات ونواة SQLite بلابياناتمسبقة/RTL/migrations، AI Hub Claudeأولًا وتثبيت عندالطلب، مركزبرامج ومثبت رسومي وهويات مستخدمين للتثبيت. مؤشراتKorkhon اختياريةداخلDEsk فقط. هذه تتقدم على نية حذفHyprland السابقة. لا تبنFullكبير.
- فُحصت plasmoids: Claude2.4.2/Codex1.2.1، izll، GPL3+. لا تُنقل أكوادها إلىMITدونمعالجةالترخيص، لا تثبتPlasma. Claudewidget يقرأOAuthcredentialويرسللـusageendpoint؛ لن نعتمدذلك. Codex يقرأlogsمحلية؛ يمكنparserمستقلopt-inمعتاريخولااختراعأرقام.
- KorkhonCUR/ANI/INF بلاLicense أوauthor؛ لا installerنُفذ. سؤالالمصدرأجاببرابطDEsk نفسه؛ الفحصلميثبتعلاقةبالمؤشرات. تبقىخارجالنشرالعامحتىترخيصحقيقي.
- فُحصتREADMEوالتراخيصالرسميةللوكلاءالستة فيwork/ai-research. ClaudeinstallerURL403لكنofficialdownloads.claude.ai manifest2.1.292متاح وبصمتهتطابقHomebrew. Claudeproprietary; Copilotcustom; Codex/GeminiApache2; OpenCode/OllamaMIT. التفاصيلفيdocs/ARCHITECTURE-ROADMAP.md. لاوكيلجديدثُبتبعدولاStudioمؤسساتكُتببعد.
- الموارد: كلاnative rootsحوالي18GiBtmpfs، DesktopSFS3.3GiB إضافية، VM4GiB، ذاكرةمتاحةنحو5GiB. pacman download cacheنُظفبعدالتثبيت(الأصولAURوDEskالموقعةباقيةcache/packages). workspace23GiBused/7.6GiBfree. يمكن إزالةSFSDesktopالمكرر بعدالتحققلأنISOيحتويه، لا تحذفISOالأصليأوالحزمالخاصة.

- UEFI actual: Plymouth quit completed successfully (about18s underTCG), SDDM Slot displayed exactly, password9b7 logged into DEsk. Renderer log explicitly says pixman and 2D Fallback. DEsk first-start rendering ongoing; screen work/desk-session-first.png. QML warnings diagnosed; minimal source corrections underway (undefinedOrientation and focus types/delegate references). SSH now works: builder localhost2232, known_hosts=/project/work/desk-known-hosts, user/password9b7. Use CtrlAltF1 forSDDM/DEsk; tty2 hasloggedin9b7. NoBIOS/newXFCE/Hyprtests yet.
- New Studio core written: nineb7/business.py independentSQLite domain, business_ui.py Arabic/English/RTL, blankorganizationonboarding, customer/productCRUD/search, atomicpostedinvoice/stock/price snapshots, audit, isolatedDemo, CSVexport, backup/restore andpersistedsettings. Originalnineb7.studio.Studio analyticsclassretained; mainlaunchesBusinessStudio. ControlCenter/Flowexistingfunctionskept.
- Tests now26passing (7new business domain), ShellCheck/Compose7passing. ActualQtfunctional business UI test passed blankfirstlaunch, ArabicRTL, records/invoice/chart, EnglishLTR and restartpersist. OriginalStudio andControlCenterGUI testsstillpassed. Screenshot work/business-ar.png; testdataintemporarydirectory, noorganizationseededintheISO. NewcorecodeNOTyetinDesktopISO.
- Pending: finishUIaudit/sourcecommit, AIHub implementation(onlyresearchdone), realDEskapps/lock/logout/network/audio, BIOS/XFCE/Hypr; graphicalinstallerandfinalDesktoprespin/release. UserdidnotauthorizedeletinganyDEandnoFullrebuild.

## 2026-10-18 — المرحلة 12: AI Hub ومركز البرامج

- عادت السحابة بعد إيقاف الحاوية؛ QEMU وtmpfs السابقان لم يستمرا. الأصلي Full وDesktop الأول محفوظان، وإعادة SHA256 لكليهما نجحت في18أكتوبر. أعيد تشغيل9b7-builder واستُخرج rootDesktop منISOالمحفوظ إلى `/tmp/9b7-iso-work/desktop-root` (8.2GiB)؛ لم يعد بناءFull.
- AI Hub مكتمل كشريحة أولية: Claude أولًا، خمسةCLIs رسمية اختيارية معversions/HTTPS/SHA256/size، تثبيت ذري لكل مستخدم، تحديث منcatalogالمراجع، إزالة تحافظعلىالمشاريعوالحسابات، اختياروكيل افتراضي وإطلاقهداخلطرفيةفيالمشروعالمختار.
- أُعيد تنفيذ --version فعليًا علىhostLinux: Claude2.1.292، Codex0.163.0، OpenCode1.19.3، Copilot1.0.98، Gemini0.64.0. لاauthentication/cloudinference مدفوع اختُبر. Gemini يحتاجNode>=20؛ optionalPTY/keychainغيرمضمنين. لاCLIsأونماذج تُحملمسبقًا فيISO.
- Ollama إدارةمحليةعندالطلب: resources/recommendation0.5B/1.5B، تأكيدحجمقبلpull،delete/unload، لا تنزيلتلقائي. CLI/نماذجOllamaداخلISOالجديدلمتختبربعد. الاستخدامClaudeمعلنغيرمتاح؛ CodexsnapshotمنمجلديختارهالمستخدممعUTCوسماتquotaفقط، دونauthfilesأوprompts. أصلحUIكانيرسلJSONإلىstatusبدلالوحةالاستخدام.
- SoftwareCenter يجمعفهرسحزمArchالموقعةويفتحsudo/pacmanبتأكيدالمستخدم؛ إزالةالمكوناتالاختياريةفقط، وتثبيتOllamaالأصلي/start/stop. launchersومكتبةDEskومركزالتحكمموصلة. NodejsأضيفلمتطلباتISO.
- 32اختبارPythonنجحوا، ShellCheckوتكوين7خدماتنجحوا؛ أصلحتSC2155فيwrapperDEsk. اختباراتQtالأربعةنجحت: legacyStudio/Flow،ControlCenter،BusinessStudioRTL/LTRوقاعدةحقيقية،AIHubتثبيتفعليلباينرياختباروإزالةوعرضusageفيGUIthread. لقطاتdocs/images/business-studio-ar.pngوai-hub.png. ليستصورمحاكاةتصميم.
- صورUEFIالأصليةPlymouth/SDDMنُقلتإلىdocs/images. جلسةDEskالسابقةشغلتFirefox/Thunar/legacyStudio؛ 2Dfallbackمثبتبالسجل. NewBusinessStudioداخلDEskلميتحققإظهارهنهائيًا؛ الصورةالمحفوظةكانتFirefoxفوقه. لاتحسبذلكنجاحًا.
- الخطوةالتالية: إصلاح/اختبارالمثبتالرسوميوهويةالتثبيت، ثمDesktopمصغرمعالأكوادالجديدةوQMLالمصحح؛ BIOS/UEFIوlock/logoutوXFCE/Hyprlandواختبارتثبيتوقرصثانٍ. VirtualBoxوالجهازالحقيقيلم يتوفرا. Releaseالأصليةمسودةناقصة؛ لا رابطتنزيلمكتملبعد.

### المرحلة 13: المثبت الرسومي — اختبارات الحماية قبل القرص

- أضيفتواجهةQtعربيةRTL/إنجليزيةLTR لاختيارالقرص(لااختيارتلقائي)،عرضالسعة/الموديل،اسممستخدموكلمةمرورجديدةوتكرارها،hostname/timezone/keyboard/session. تأكيدنهائييلزم`ERASE /dev/DEVICE`باسم القرصالفعلينفسه. القرصالـmounted/read-onlyغيرقابلللاختيار،وbackendيعيدالتحقققبلالكتابة.
- backendPythonيستخدمrsyncمنSquashFSالأصلية،GRUBBIOS+UEFI،حسابًاخاصًاولايثبّت9b7/9b7كحسابدائم،يمررpasswordعبرstdinلـchpasswdفقط،ويمنعfirstbootمنإعادةحسابالتجربة. لاpasswordفيargvأوالسجلاتأوملفمؤقت. لاDualBoot. لايدعيفشلتثبيتأنه نجح.
- UIيتحققبـsudoثميرسلالإعداداتعبرpipeبعدنجاحالمصادقة؛ لايفتحGUIكـroot. تأكيدالإزالةوالمصادقةخطوتانمنفصلتان. 35اختبارمصدرنجحواوShellCheck/Compose7،واختبارQtأثبتمنعقرصغيرمختار/تأكيدقرصآخرودعماللغتين. لمتُكتبأقراصفيهذهالاختبارات؛ التثبيتالحقيقيمازالقيدالاختبار.
- /etc/os-releaseأضيفبالاسم9b7/ID_LIKE=arch؛ لاشعارجديد.
- استعادةالحاويةاحتفظتبشبكةbridgeلاتصلللproxyبعدإعادةالسحابة. أمرcurlداخلsidecarبـnetworkhostوPIDnamespaceالـbuilderوملفاتهنجحمعTLS؛ لاغلقللتحقق. استُخدمتnamespaceمؤقتةلشبكةالبناءفقط. لايُنقلproxyأوشهاداتهإلىISOالمستخدم.
- صلاحيةReleaseماتزال401عبرuploads.github.com،معنجاحgitpush. طلبناسرGH_UPLOAD_TOKENفيإعداداتالبيئةبصلاحيةContentsوليسداخلchat؛ حُفظاحتياجهلـapi.github.com وuploads.github.com. لاالمسودةالناقصةنُشرتولاتنزيلمكتملادُّعي.

- بناءDesktopيُستكملبـscripts/repack-desktop.shمعإبقاءالأصلين؛ scriptيفحصSHAومصدرrootويعيدإنشاءFATUEFIبالـkernel/initramfsالمطابقينللتحديث،لايكتفيبتحديثBIOS. احتفاظUUIDالإقلاعقديممقصودلتوافقخياراتarchisosearchuuid؛اسمISOالجديديحمل18أكتوبر. سُدّنقصفعليفيGitHubActions: بناءحزمةDEskكانغيرمضافقبلbuild-iso.
- Node24منArchوتحديثاتالنظامنُصبتبتوقيعاتمتحققة؛ kernelتحدثلذلكيلزمتحديثEFIأيضًا. Landlockغيرمدعومفيkernelالسحابةفاستُخدم--disable-sandboxلهذهعمليةpacmanفيbuilderفقط؛ TLSوتوقيعاتالحزملمتُعطل. شهادةproxyعامةمؤقتةللبناءتُزالقبلالضغطومفتاحpacmanالخاصيبقىخارجISO.
- المستخدمقدمتوكنرفعآخر؛ تمتمريرهلمهمةرفعطويلةالعمرعبرpromptمخفي،لافيargvأوملف. لاتكررطلبالتوكن. يفحصالرفعالصغيرأولًا؛السرمحفوظذاكرةالعمليةفقطوقديضيععندإيقافالبيئة. scripts/release-iso.pyيدعمGH_UPLOAD_TOKENوsidecarمرجعالمصدرالخاصبكلISO.
