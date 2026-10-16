# استخدام 9b7 Linux

المستخدم وكلمة مرور Linux: **9b7 / 9b7**. الحساب ضمن wheel وdocker؛ هذه إعدادات معمل مشروع تخرج. لا توجد خدمة SSH مفعلة افتراضيًا.

## البداية

افتح 9b7 BIS Studio من القائمة أو `Super+S`. زر **Run demo** يستورد `data/demo-sales.csv`: 8 طلبات، إيراد 39100، تكلفة 17000، ربح 22100، هامش 56.52%. الأرقام بعملة dataset نفسها وليست تحويلًا لعملة محددة.

أداة **9b7 Flow** هي مساهمة المشروع الأصلية: تحقق من صفوف CSV، ETL إلى SQLite، كشف التكرار والتعارض، سجل تدقيق، ومخرجات HTML/JSON. التطبيق المكتبي **BIS Studio** واجهة أصلية لهذه الدورة وإدارة الخدمات وقواعد البيانات ووكلاء AI.

```bash
9b7-flow run ~/sales.csv
9b7-flow run ~/sales.csv --strict
9b7-flow history
9b7-flow report
```

الأعمدة المطلوبة: `order_id,date,customer,product,quantity,unit_price,unit_cost`. التاريخ ISO مثل `2026-10-16`. صف واحد لكل order_id. المبالغ تُخزن بسنتات صحيحة لتفادي أخطاء float. يرجع الأمر 2 إذا اكتمل مع صفوف مرفوضة، 1 عند الفشل، و0 عند نجاح كامل. وضع strict يرفض المعاملة كاملة عند خطأ أو تعارض.

البيانات والتقارير في `~/.local/state/9b7`. نقل CSV إلى `~/9b7-Inbox` يشغّل أتمتة المجلد عبر systemd user؛ انقل الملف باسم مؤقت ثم أعد تسميته إلى `.csv` بعد اكتمال نسخه. الملفات تُنقل إلى processed أو review أو failed، مع تقرير مستقل لكل تشغيل. لا يوجد حذف تلقائي لسجل الأعمال.

## الخدمات

شغّل واحدة في كل مرة من **Lab services** أو `9b7-services start NAME`. أمر stop يحافظ على بيانات Docker volumes.

| الاسم | منفذ محلي | الدخول الأول | تقدير RAM |
|---|---|---|---|
| n8n | 5678 | أنشئ حسابًا من شاشة التطبيق؛ كلمة المرور تتبع قواعد n8n | 0.7GB |
| superset | 8088 | `9b7 / 9b7` | 2GB |
| metabase | 3000 | معالج أول تشغيل لإنشاء حسابك | 1.8GB |
| odoo | 8069 | أنشئ قاعدة؛ master password هي `9b7` | 1.6GB |
| erpnext | 8080 | اسم الدخول المفروض من Frappe: `Administrator`، كلمة المرور `9b7` | 3.5GB+ |
| ai | 11434 | Ollama محلي، دون API key | 2GB+ |
| databases | 5432 / 9042 / 6379 | PostgreSQL `9b7/9b7` وdatabase `bis`؛ Cassandra/Redis معمل محلي | 3GB |

المنافذ مربوطة بـ127.0.0.1. الخدمات لا تبدأ كلها مع الإقلاع. Docker يشتغل لكن مجموعات التطبيقات تبدأ عند الطلب. التهيئة الأولى لـERPNext وMetabase قد تستغرق عدة دقائق.

## قواعد البيانات في تطبيق واحد

Database console تدعم SQLite، PostgreSQL، MySQL/MariaDB، Cassandra، MongoDB، Redis. ليست وعدًا بدعم كل محرك موجود. DBeaver موجود كأداة إضافية لـSQL/JDBC؛ دعم Cassandra هنا داخل Studio، ولا يعتمد على إضافات DBeaver المدفوعة.

- SQLite: مسار الملف؛ مثال `SELECT product, SUM(quantity) FROM orders GROUP BY product`.
- PostgreSQL: `postgresql://9b7:9b7@localhost:5432/bis`.
- MySQL/MariaDB: `mysql://user:password@localhost:3306/database`.
- Cassandra: `cassandra://localhost:9042/system`؛ مثال `SELECT cluster_name FROM local`.
- MongoDB: URI بقاعدة افتراضية، وطلب JSON مثل `{"collection":"sales","filter":{}}`.
- Redis: `redis://localhost:6379/0`؛ طلب مثل `{"get":"key"}` أو `{"scan":"sales:*"}`.

الواجهة للقراءة حتى 200 صف؛ بيانات الاتصال في الذاكرة ولا تُحفظ. استخدم حساب قاعدة مخصصًا للقراءة عند الاتصال ببيانات حقيقية. أدوات الإدارة الأصلية متاحة للكتابة.

## AI team

ابدأ `ai`، ثم حلّل التقرير في Studio. النموذج `qwen2.5:1.5b` مناسب نسبيًا لـ8GB ويعمل على CPU. ثلاثة أدوار: محلل، مخطط عمليات، مراجع. لا ينفّذون أوامر أو يغيّرون بيانات؛ يمرّرون المؤشرات الإجمالية فقط، ويعرضون اقتراحات للمراجعة. جودة النموذج الصغير محدودة ويجب مراجعة الأرقام والتوصيات.

## الاختصارات

`Super+Enter` Terminal، `Super+D` قائمة، `Super+B` Firefox، `Super+C` VSCodium، `Super+E` ملفات، `Super+S` Studio، `Super+Q` إغلاق، `Super+F` ملء الشاشة، `Super+L` قفل، `Super+1..9` مساحات عمل، `Super+Shift+1..9` نقل نافذة. `Alt+Shift` يبدل لوحة المفاتيح عربي/إنجليزي. `Print` لقطة منطقة إلى clipboard.

Wireshark وBurp Suite أدوات المختبر الأمني. Burp قد يعرض اتفاقيته عند أول تشغيل. Obsidian لتوثيق المشروع؛ Firefox جاهز للتصفح. تراخيص كل تطبيق مستقلة.
