from django.db import models

class ExcelFile(models.Model):

    file = models.FileField(upload_to='excel_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'excelTable'


# Applicator [views_sparepart.py]

class ApplicatorPart(models.Model):
    applicatorNumber = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        db_table = 'aplicatorPart'

class PartName(models.Model):
    partName = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        db_table = 'partName'

class PartDesk(models.Model):
    partName = models.ForeignKey(PartName, on_delete=models.SET_NULL, null=True, blank=True)
    applicatorNumber = models.ForeignKey(ApplicatorPart, on_delete=models.SET_NULL, null=True, blank=True)
    partNumber = models.CharField(max_length=255, blank=True, null=True)
    partCode = models.CharField(max_length=255, blank=True, null=True)
    level = models.CharField(max_length=255, blank=True, null=True)
    marking = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        db_table = 'partDesk'

# CARLINE SPP MCL import [views.py]
class Carline(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Nama yang unik sebagai primary key
    
    class Meta:
        db_table = 'carline'
    def __str__(self):
        return self.name
    
# spp
class Bulan(models.Model):
    carline = models.ForeignKey(Carline, on_delete=models.CASCADE, related_name='bulans', null=True)
    JAN = models.IntegerField(null=True, blank=True)
    FEB = models.IntegerField(null=True, blank=True)
    MAR = models.IntegerField(null=True, blank=True)
    APR = models.IntegerField(null=True, blank=True)
    MAY = models.IntegerField(null=True, blank=True)
    JUN = models.IntegerField(null=True, blank=True)
    JUL = models.IntegerField(null=True, blank=True)
    AUG = models.IntegerField(null=True, blank=True)
    SEP = models.IntegerField(null=True, blank=True)
    OCT = models.IntegerField(null=True, blank=True)
    NOV = models.IntegerField(null=True, blank=True)
    DEC = models.IntegerField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True) 

    class Meta:
        db_table = 'bulan'

    def __str__(self):
        return f"{self.carline.name} - {self.year}"

    
class NoAssy(models.Model):
    noAssy = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        db_table = 'noAssy'

    def __str__(self):
        return f"NoAssy {self.id}"

class Quantity(models.Model):
    carline = models.ForeignKey(Carline, on_delete=models.CASCADE, related_name='quantities', null=True)
    bulan = models.ForeignKey(Bulan, on_delete=models.CASCADE, related_name='quantities', null=True)
    noAssy = models.ForeignKey(NoAssy, on_delete=models.CASCADE, related_name='quantities', null=True)
    month = models.CharField(max_length=3, choices=[
        ('JAN', 'January'),
        ('FEB', 'February'),
        ('MAR', 'March'),
        ('APR', 'April'),
        ('MAY', 'May'),
        ('JUN', 'June'),
        ('JUL', 'July'),
        ('AUG', 'August'),
        ('SEP', 'September'),
        ('OCT', 'October'),
        ('NOV', 'November'),
        ('DEC', 'December')
    ])
    year = models.IntegerField(null=True, blank=True)  # <<--- Tambahan baru
    value = models.IntegerField()

    class Meta:
        db_table = 'isiBulan'

    def __str__(self):
        return f"{self.bulan} - {self.month} {self.year}: {self.value}"

# mcl

class MachineLoading(models.Model):
    carline = models.ForeignKey(Carline, on_delete=models.CASCADE, related_name='machineLoading', null=True )
    machine = models.CharField(max_length=255, blank=True, null=True)
    noControl = models.CharField(max_length=255, blank=True, null=True)
    kind = models.CharField(max_length=255, blank=True, null=True)
    size = models.CharField(max_length=255, blank=True, null=True)
    twist = models.CharField(max_length=255, blank=True, null=True)
    termB = models.CharField(max_length=255, blank=True, null=True)
    manB = models.CharField(max_length=255, blank=True, null=True)
    accB1 = models.CharField(max_length=255, blank=True, null=True)
    termA = models.CharField(max_length=255, blank=True, null=True)
    manA = models.CharField(max_length=255, blank=True, null=True)
    accA1 = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'machine_loading'

    def __str__(self):
        return f"Machine Loading for {self.carline.name}"

class AssyValue(models.Model):
    noAssy = models.CharField(max_length=255, blank=True, null=True)
    noControl = models.ForeignKey(MachineLoading, on_delete=models.CASCADE, related_name='assy_values', null=True)
    termB = models.ForeignKey(MachineLoading, on_delete=models.CASCADE, related_name='assy_value_termB_results', null=True)
    termA = models.ForeignKey(MachineLoading, on_delete=models.CASCADE, related_name='assy_value_termA_results', null=True)
    value = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'assy_value'

    def __str__(self):
        return f"{self.noAssy} - {self.value}"

# model calculation part 1
from datetime import datetime

class CalculationResult(models.Model):
    carline = models.ForeignKey(Carline, on_delete=models.CASCADE, related_name='calculation_results', null=True)
    noControl = models.ForeignKey(MachineLoading, on_delete=models.CASCADE, related_name='calculation_no_control_results', null=True)
    termB = models.ForeignKey(MachineLoading, on_delete=models.CASCADE, related_name='calculation_termB_results', null=True)
    termA = models.ForeignKey(MachineLoading, on_delete=models.CASCADE, related_name='calculation_termA_results', null=True)
       
    month = models.CharField(max_length=3, choices=[
        ('JAN', 'January'),
        ('FEB', 'February'),
        ('MAR', 'March'),
        ('APR', 'April'),
        ('MAY', 'May'),
        ('JUN', 'June'),
        ('JUL', 'July'),
        ('AUG', 'August'),
        ('SEP', 'September'),
        ('OCT', 'October'),
        ('NOV', 'November'),
        ('DEC', 'December')
    ])
    year = models.IntegerField(default=datetime.now().year)
    result = models.IntegerField()

    class Meta:
        db_table = 'calculation_result'
        unique_together = ('carline', 'noControl', 'month', 'year')  # Unik berdasarkan carline, noControl, bulan, tahun

    def __str__(self):
        return f"{self.carline.name} - {self.noControl} ({self.month} {self.year}): {self.result}"

# model calculation part 2

class CalculationResultLoading(models.Model):
    carline = models.ForeignKey(Carline, on_delete=models.CASCADE, related_name='calculation_results_loading', null=True)
    terminal = models.CharField(max_length=255)
    month = models.CharField(max_length=10)
    year = models.IntegerField(default=datetime.now().year)
    result = models.FloatField()

    class Meta:
        db_table = 'calculation_result_loading'

    def __str__(self):
        return f"{self.carline.name} - {self.terminal} ({self.month})"

# Stroke Part
class Load_applicator(models.Model):
    name = models.CharField(max_length=100)
    loading = models.IntegerField()
    image = models.ImageField(upload_to='applicator_images/', blank=True, null=True)  # New image field

    class Meta:
        db_table = 'stroke'

    def __str__(self):
        return self.name
        
# model calculation part 3
class AggregatedResultByTerminal(models.Model):
    calculation_result = models.ForeignKey(CalculationResultLoading, on_delete=models.SET_NULL, null=True, blank=True)
    terminal = models.CharField(max_length=100)
    month = models.CharField(max_length=10)
    total_result = models.FloatField()
    
    class Meta:
        db_table = 'aggregated_result_terminal'
        ordering = ['terminal', 'month']

    def __str__(self):
        return f'{self.terminal} - {self.month}: {self.total_result}'

# hitung load appclicator X AggregatedResultByTerminal
class TerminalNameMapping(models.Model):
    calculation_result = models.ForeignKey(CalculationResultLoading, on_delete=models.CASCADE, null=True)
    terminal = models.ForeignKey(AggregatedResultByTerminal, on_delete=models.CASCADE, related_name='terminal_mapping', null=True)
    name = models.ForeignKey(Load_applicator, on_delete=models.CASCADE, related_name='applicator_mapping', null=True)
    month = models.ForeignKey(AggregatedResultByTerminal, on_delete=models.CASCADE, related_name='month_mapping', null=True)
    total_result = models.ForeignKey(AggregatedResultByTerminal, on_delete=models.CASCADE, related_name='aggregate', null=True)
    last_loading = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'terminal_name_mapping'

    def __str__(self):
        return f"{self.terminal.terminal} - {self.name.name} - {self.month.month}"

class LastRoundup(models.Model):
    calculation_result = models.ForeignKey(CalculationResultLoading, on_delete=models.CASCADE, null=True)
    terminal = models.ForeignKey(AggregatedResultByTerminal, on_delete=models.CASCADE, related_name='terminal_roundup', null=True)
    name = models.ForeignKey(Load_applicator, on_delete=models.CASCADE, related_name='applicator_roundup', null=True)
    month = models.ForeignKey(AggregatedResultByTerminal, on_delete=models.CASCADE, related_name='month_roundup', null=True)
    rounded_loading = models.FloatField(null=True, blank=True)
    year = models.IntegerField(default=datetime.now().year)

    class Meta:
        db_table = 'last_roundup'

    def __str__(self):
        return f"{self.terminal.terminal} - {self.name.name} - {self.month.month}"

class LoadingPartResult(models.Model):
    carline = models.ForeignKey(Carline, on_delete=models.CASCADE)
    part_name = models.CharField(max_length=255)
    terminal = models.CharField(max_length=255)
    month = models.CharField(max_length=10)  # e.g., "JAN", "FEB"
    last_loading = models.FloatField(null=True, blank=True)
    rounded_loading = models.FloatField(null=True, blank=True)
    average = models.FloatField(null=True, blank=True)
    average_round = models.FloatField(null=True, blank=True)  # ➕ Tambahan
    partdesk = models.ForeignKey('PartDesk', null=True, blank=True, on_delete=models.SET_NULL)
    year = models.IntegerField(default=datetime.now().year)

    class Meta:
        db_table = 'loading_part_result'
        unique_together = ('carline', 'part_name', 'terminal', 'month')

from datetime import datetime

class Departement(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
        
    class Meta: 
        db_table = 'departement' 

class Section(models.Model):
    name = models.CharField(max_length=255)
    departement = models.ForeignKey(Departement, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'section' 

class PurchaseRequest(models.Model):
    registered_no = models.CharField(max_length=100, unique=True)
    departement = models.ForeignKey(Departement, on_delete=models.SET_NULL, null=True, blank=True)
    section = models.ForeignKey('Section', on_delete=models.CASCADE)
    purchase_by = models.CharField(max_length=100)
    requested = models.BooleanField(default=False)
    part_order = models.ManyToManyField(Carline)
    total_amount = models.FloatField(default=0) 
    date = models.DateField(auto_now_add=True)

    approve_spv = models.BooleanField(null=True, blank=True)
    approve_sspv = models.BooleanField(null=True, blank=True)

    def __str__(self):
        return f"Request {self.registered_no} by {self.purchase_by}"

    class Meta:
        db_table = 'purchase_request'

from datetime import date

class RequestItem(models.Model):
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='items', null=True, blank=True)
    loading_part_result = models.ForeignKey(LoadingPartResult, on_delete=models.CASCADE)
    budget_ref_no = models.CharField(max_length=100)
    result_average_round = models.FloatField(default=0)
    estimated_price = models.FloatField(default=0)
    amount = models.FloatField(default=0)
    deadline = models.DateField(null=True, blank=True)

    class Meta:
        
        db_table = 'request_form'


    def __str__(self):
        return f"Item for Request {self.purchase_request.registered_no if self.purchase_request else 'N/A'}"

from django.db import models

class Supplier(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    tel_no = models.CharField(max_length=100, unique=True)
    fax_no = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'supplier'

    def __str__(self):
        return self.name


class PurchaseOrder(models.Model):
    registered_no = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    term = models.CharField(max_length=100)
    delivery = models.DateField(null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    shipped_by = models.CharField(max_length=100)
    
    def __str__(self):
        return f"Request {self.registered_no}"

    class Meta:
        db_table = 'purchase_order'