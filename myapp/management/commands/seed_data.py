from django.core.management.base import BaseCommand
from myapp.models import Carline, Departement, Section, Supplier, Shipped

class Command(BaseCommand):
    help = 'Seed initial data for master tables'

    def handle(self, *args, **kwargs):
        # Seed Carline
        carlines = ['CARL-HND', 'CARL-HRV', 'CARL-CVC', 'CARL-CRV', 'CARL-MBL']
        for name in carlines:
            Carline.objects.get_or_create(name=name)
        self.stdout.write(self.style.SUCCESS("✅ Carline seeded."))

        # Seed Departement
        departements = ['Production', 'Maintenance', 'Purchasing', 'Stock Control']
        dept_objs = {}
        for name in departements:
            obj, created = Departement.objects.get_or_create(name=name)
            dept_objs[name] = obj
        self.stdout.write(self.style.SUCCESS("✅ Departement seeded."))

        # Seed Section
        section_names = ['Purchase Planning', 'Goods Receiving', 'Assembly']
        for dept in dept_objs.values():  # dept_objs dibuat saat seeding Departement
            for section_name in section_names:
                Section.objects.get_or_create(name=section_name, departement=dept)
        self.stdout.write(self.style.SUCCESS("✅ Section (3 x 4) seeded."))

        # Seed Supplier
        suppliers = [
            {
                'name': 'Bima Industrial Co., Ltd.',
                'email': '2141720255@student.polinema.ac.id',
                'address': '1-2-3 Chiyoda, Tokyo, Japan',
                'tel_no': '+81-3-1234-5678',
                'fax_no': '+81-3-8765-4321',
                'attn': 'Mr. Tannn',
                'cc': 'sales@alpha-industrial.co.jp'
            },
            {
                'name': 'Zaaf Engineering GmbH',
                'email': 'zaafaraniperfume@gmail.com',
                'address': 'Berliner Straße 22, 10115 Berlin, Germany',
                'tel_no': '+49-30-123456',
                'fax_no': '+49-30-654321',
                'attn': 'Frau Müller',
                'cc': 'support@beta-eng.de'
            },
            {
                'name': 'Gamma Technologies Inc.',
                'email': 'support@gammatech.com',
                'address': '500 Market Street, San Francisco, CA, USA',
                'tel_no': '+1-415-555-1234',
                'fax_no': '+1-415-555-4321',
                'attn': 'John Smith',
                'cc': 'john.smith@gammatech.com'
            },
            {
                'name': 'Delta Components Ltd.',
                'email': 'contact@deltacomponents.co.uk',
                'address': '75 Oxford Street, London, W1D 2ES, United Kingdom',
                'tel_no': '+44-20-7946-0958',
                'fax_no': '+44-20-7946-0959',
                'attn': 'Ms. Taylor',
                'cc': 'taylor@deltacomponents.co.uk'
            },
            {
                'name': 'Epsilon Precision Sdn. Bhd.',
                'email': 'sales@epsilon.my',
                'address': 'Lot 45, Jalan Industri 3, Shah Alam, Malaysia',
                'tel_no': '+60-3-5511-2233',
                'fax_no': '+60-3-5511-3344',
                'attn': 'Encik Rahman',
                'cc': 'rahman@epsilon.my'
            }
        ]
        for data in suppliers:
            Supplier.objects.get_or_create(**data)
        self.stdout.write(self.style.SUCCESS("✅ 5 International Suppliers seeded."))



        # Seed Shipped - international logistics companies
        shipped_names = [
            'DHL Express',           # Germany-based, global express delivery
            'FedEx International',   # US-based global logistics
            'UPS Worldwide',         # United Parcel Service, global shipping
            'Maersk Line',           # Denmark, top global sea freight company
            'DB Schenker',           # Germany, integrated logistics services
            'Kuehne + Nagel',        # Switzerland, supply chain logistics
            'Nippon Express',        # Japan-based freight and logistics
            'Yang Ming Marine Transport', # Taiwan, container shipping
        ]
        for name in shipped_names:
            Shipped.objects.get_or_create(name=name)
        self.stdout.write(self.style.SUCCESS("✅ International Shipped options seeded."))

