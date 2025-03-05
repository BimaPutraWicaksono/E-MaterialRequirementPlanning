from django.db.models.signals import post_save, post_delete
from django.db.models import Sum
from django.dispatch import receiver
from .models import CalculationResultLoading, AggregatedResultByTerminal


# Sinyal untuk pembaruan atau penambahan data di CalculationResultLoading
@receiver(post_save, sender=CalculationResultLoading)
def update_aggregated_results(sender, instance, **kwargs):
    terminal = instance.terminal
    month = instance.month

    # Hitung total result berdasarkan terminal dan bulan
    total_result = CalculationResultLoading.objects.filter(
        terminal=terminal,
        month=month
    ).aggregate(total_result=Sum('result'))['total_result']

    # Update atau buat data di AggregatedResultByTerminal
    AggregatedResultByTerminal.objects.update_or_create(
        terminal=terminal,
        month=month,
        defaults={'total_result': total_result}
    )

# Sinyal untuk menghapus data di AggregatedResultByTerminal saat CalculationResultLoading dihapus
@receiver(post_delete, sender=CalculationResultLoading)
def delete_aggregated_results(sender, instance, **kwargs):
    terminal = instance.terminal
    month = instance.month

    # Hapus data dari AggregatedResultByTerminal jika tidak ada lagi CalculationResultLoading untuk terminal dan bulan tersebut
    if not CalculationResultLoading.objects.filter(terminal=terminal, month=month).exists():
        AggregatedResultByTerminal.objects.filter(terminal=terminal, month=month).delete()
