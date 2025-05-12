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

    class Meta:
        db_table = 'janDec'

    def __str__(self):
        return f"Bulan {self.id}"
    
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
    value = models.IntegerField()

    class Meta:
        db_table = 'isiBulan'  # Sesuaikan nama tabel jika perlu

    def __str__(self):
        return f"{self.bulan} - {self.month}: {self.value}"


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
    
    result = models.IntegerField()

    class Meta:
        db_table = 'calculation_result'
        unique_together = ('carline', 'noControl', 'month')  # Kombinasi carline, noControl, dan month harus unik

    def __str__(self):
        return f"Result for {self.carline.name} - {self.noControl} ({self.month}): {self.result}"

# model calculation part 2

class CalculationResultLoading(models.Model):
    carline = models.ForeignKey(Carline, on_delete=models.CASCADE, related_name='calculation_results_loading', null=True)
    terminal = models.CharField(max_length=255)
    month = models.CharField(max_length=10)
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

    class Meta:
        db_table = 'last_roundup'

    def __str__(self):
        return f"{self.terminal.terminal} - {self.name.name} - {self.month.month}"

# views calculate in dashboard

class ViewsCalculateLoad(models.Model):
    machine_number = models.CharField(max_length=100)
    name_dash = models.CharField(max_length=255, blank=True, null=True)
    number_dash = models.CharField(max_length=255, blank=True, null=True)
    level_dash = models.CharField(max_length=100, blank=True, null=True)
    source = models.CharField(max_length=50)
    january_dash = models.IntegerField(blank=True, null=True)
    february_dash = models.IntegerField(blank=True, null=True)
    march_dash = models.IntegerField(blank=True, null=True)
    april_dash = models.IntegerField(blank=True, null=True)
    may_dash = models.IntegerField(blank=True, null=True)
    june_dash = models.IntegerField(blank=True, null=True)
    july_dash = models.IntegerField(blank=True, null=True)
    august_dash = models.IntegerField(blank=True, null=True)
    september_dash = models.IntegerField(blank=True, null=True)
    oktober_dash = models.IntegerField(blank=True, null=True)
    november_dash = models.IntegerField(blank=True, null=True)
    december_dash = models.IntegerField(blank=True, null=True)
    average_dash = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = 'views_calculate_load'

    def __str__(self):
        return f'{self.machine_number} - {self.source}'

#  model gabungan applicator dan nilainya

class CombinedModel(models.Model):
    last_roundup = models.ForeignKey(LastRoundup, on_delete=models.CASCADE, related_name='combined_last_roundup')
    part_desk = models.ForeignKey(PartDesk, on_delete=models.CASCADE, related_name='combined_part_desk')

    class Meta:
        db_table = 'combined_model'
    
    def __str__(self):
        return f"{self.last_roundup.terminal.terminal} - {self.last_roundup.name.name} - {self.last_roundup.month.month} - {self.part_desk.partNumber}"

# apllicator part loading dengan average

from django.db import models

class ApplicatorPartAvarage(models.Model):
    carline = models.ForeignKey(Carline, on_delete=models.CASCADE, related_name='carline_avarage', null=True)
    terminal = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    part_number = models.CharField(max_length=100)
    part_code = models.CharField(max_length=100, blank=True, null=True)
    level = models.CharField(max_length=10, blank=True, null=True)
    marking = models.CharField(max_length=100, blank=True, null=True)
    jan = models.CharField(max_length=10, blank=True, null=True)
    feb = models.CharField(max_length=10, blank=True, null=True)
    mar = models.CharField(max_length=10, blank=True, null=True)
    apr = models.CharField(max_length=10, blank=True, null=True)
    may = models.CharField(max_length=10, blank=True, null=True)
    jun = models.CharField(max_length=10, blank=True, null=True)
    jul = models.CharField(max_length=10, blank=True, null=True)
    aug = models.CharField(max_length=10, blank=True, null=True)
    sep = models.CharField(max_length=10, blank=True, null=True)
    oct = models.CharField(max_length=10, blank=True, null=True)
    nov = models.CharField(max_length=10, blank=True, null=True)
    dec = models.CharField(max_length=10, blank=True, null=True)
    average = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = 'applicator_part_average'

    def __str__(self):
        return f"{self.terminal} - {self.name} - {self.part_number}" 

# result [views_sparepart.py]
class Item(models.Model):
    
    machineNumber = models.IntegerField(default=0)
    nameDash = models.CharField(max_length=100)
    numberDash = models.IntegerField()
    levelDash = models.CharField(max_length=100)
    categoryDash = models.CharField(max_length=100)
    januaryDash = models.IntegerField(default=0)
    februaryDash = models.IntegerField(default=0)
    marchDash = models.IntegerField(default=0)
    aprilDash = models.IntegerField(default=0)
    mayDash = models.IntegerField(default=0)
    juneDash = models.IntegerField(default=0)
    julyDash = models.IntegerField(default=0)
    augustDash = models.IntegerField(default=0)
    septemberDash = models.IntegerField(default=0)
    octoberDash = models.IntegerField(default=0)
    novemberDash = models.IntegerField(default=0)
    decemberDash = models.IntegerField(default=0)
    averageDash = models.IntegerField(default=0)
    description = models.TextField()

    class Meta:
        db_table = 'dashboard'
        
    def __str__(self):
        return self.nameDash
    
# order [views_order]

class PurchaseReq(models.Model):
    
    registeredNo = models.CharField(max_length=100)
    deptartemen = models.CharField(max_length=100)
    section = models.CharField(max_length=100)
    purchaseReqBy = models.CharField(max_length=100)
    budgetReqNo = models.IntegerField(default=0)
    estimatedPrice = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    totalAmount = models.DecimalField(max_digits=10, decimal_places=2)
    
    machineNumber = models.IntegerField(default=0)
    nameDash = models.CharField(max_length=100)
    averageDash = models.IntegerField(default=0)
    carlines = models.ManyToManyField('Carline', blank=True)

    class Meta:
        db_table = 'purchaseReq'

    def __str__(self):
        return self.nameDash
