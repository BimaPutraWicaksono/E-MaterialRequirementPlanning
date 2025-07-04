from django.shortcuts import render, redirect, get_object_or_404
from .models import Carline, MachineLoading, AssyValue, NoAssy, Bulan, Quantity
from django.http import JsonResponse
from django.contrib import messages
from .form import CarlineForm, UploadFileForm
import pandas as pd
import logging
import openpyxl
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from myproject.decorators import group_required

logger = logging.getLogger(__name__)

# carline view (add carline)
@login_required()
def carline_view(request):
    if request.method == 'POST':
        form = CarlineForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('carline')
    else:
        form = CarlineForm()

    query = request.GET.get('q', '')
    if query:
        carlines = Carline.objects.filter(name__icontains=query).order_by('name')  # Sort filtered carlines A-Z
    else:
        carlines = Carline.objects.all().order_by('name')  # Sort all carlines A-Z

    context = {
        'form': form,
        'carlines': carlines,
    }
    return render(request, 'carline.html', context)


# Produksi Plan QTY tampilan all
@login_required()
def allSixProductionPlan(request):
    # Mengambil semua data Bulan, diurutkan berdasarkan carline
    all_bulan = Bulan.objects.select_related('carline').all().order_by('carline__name')

    context = {
        'all_bulan': all_bulan
    }

    return render(request, 'allSixProductionPlan.html', context)

        
from django.urls import reverse

@login_required()
def delete_carline(request, pk):
    carline = get_object_or_404(Carline, pk=pk)
    carline_name = carline.name
    carline.delete()
    messages.success(request, f'Carline {carline_name} has been deleted along with related entries.')
    return redirect(reverse('carline'))

@login_required()
def reset_carline_all(request):
    if request.method == 'POST':
        # Menghapus seluruh data dari model Carline
        Carline.objects.all().delete()
        messages.success(request, 'All Carline data has been deleted along with related entries.')
        return redirect(reverse('carline'))  # Redirect ke halaman setelah data dihapus
    return redirect(reverse('carline'))  # Redirect jika metode bukan POST

# import excel SPP(six produc plan)
@login_required()
def sixProductionPlan(request, name):
    carline = get_object_or_404(Carline, name=name)

    if request.method == 'POST':
        if 'import' in request.POST:
            form = UploadFileForm(request.POST, request.FILES)
            if form.is_valid():
                files = request.FILES.getlist('file')
                sheet_name = form.cleaned_data.get('sheet_name')

                for file in files:
                    try:
                        # Baca data utama (mulai dari baris 13 karena header=[12,13])
                        if sheet_name:
                            df = pd.read_excel(file, sheet_name=sheet_name, header=[12, 13])
                            sheet_for_year = pd.read_excel(file, sheet_name=sheet_name, header=None, nrows=8)
                        else:
                            df = pd.read_excel(file, header=[12, 13])
                            sheet_for_year = pd.read_excel(file, header=None, nrows=8)

                        # Ambil tahun dari sel E8 (baris ke-7, kolom ke-4)
                        try:
                            year_cell = sheet_for_year.iloc[7, 4]  # E8
                            year = int(str(year_cell).strip()) if pd.notna(year_cell) else None
                        except Exception:
                            year = None

                        months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                                  'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
                        prod_columns = [(month, 'Prod') for month in months if (month, 'Prod') in df.columns]

                        if not prod_columns:
                            messages.error(request, "Tidak ada kolom 'Prod' yang ditemukan di bawah kolom bulan.")
                            return redirect('sixProductionPlan', name=carline.name)

                        prod_values = []
                        for month, prod_col in prod_columns:
                            prod_values.append(df[(month, 'Prod')].tolist())

                        combined_prod_values = sum(prod_values, [])

                        headers = df.columns.tolist()
                        month_map = {month: month for month in months}

                        no_assy_column_index = 4

                        for index, row in df.iterrows():
                            no_assy_value = row.iloc[no_assy_column_index] if no_assy_column_index < len(row) else None
                            if no_assy_value is None or pd.isna(no_assy_value) or str(no_assy_value).strip() == "":
                                messages.error(request, f"Empty or missing noAssy at row {index}. Stopping import.")
                                break

                            no_assy, _ = NoAssy.objects.get_or_create(noAssy=no_assy_value)
                            bulan_data = {month: None for month in month_map.keys()}

                            for (month, prod_col) in prod_columns:
                                value = row[(month, 'Prod')]
                                if pd.notna(value) and str(value).strip():
                                    try:
                                        bulan_data[month_map[month]] = int(value)
                                    except ValueError:
                                        bulan_data[month_map[month]] = None

                            bulan, _ = Bulan.objects.get_or_create(carline=carline, year=year, **bulan_data)

                            for month in bulan_data.keys():
                                value = bulan_data[month]
                                if value is not None:
                                    quantity_exists = Quantity.objects.filter(
                                        bulan=bulan,
                                        noAssy=no_assy,
                                        month=month,
                                        carline=carline,
                                        year=year
                                    ).exists()
                                    if not quantity_exists:
                                        Quantity.objects.create(
                                            bulan=bulan,
                                            noAssy=no_assy,
                                            month=month,
                                            value=value,
                                            carline=carline,
                                            year=year
                                        )

                    except Exception as e:
                        messages.error(request, f"Gagal membaca file Excel: {e}")

            return redirect('sixProductionPlan', name=carline.name)

        elif 'reset' in request.POST:
            Bulan.objects.filter(carline=carline).delete()
            Quantity.objects.filter(carline=carline).delete()
            NoAssy.objects.filter(id__in=Quantity.objects.filter(carline=carline).values_list('noAssy_id', flat=True)).delete()
            messages.success(request, f"Data untuk carline {carline.name} telah direset.")
            return redirect('sixProductionPlan', name=carline.name)

    bulan_list = Bulan.objects.filter(carline=carline)
    months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
              'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    columns = {month: bulan_list.filter(**{month: None}).count() == 0 for month in months}

    context = {
        'bulan_list': bulan_list,
        'form': UploadFileForm(),
        'carline': carline,
        'columns': columns
    }
    return render(request, 'sixProductionPlan.html', context)

@login_required()
def reset_sixProductionPlan(request, name):
    carline = get_object_or_404(Carline, name=name)
    
    # Ambil semua noAssy_id yang terkait dengan carline sebelum data Quantity dihapus
    no_assy_ids = Quantity.objects.filter(carline=carline).values_list('noAssy_id', flat=True)

    # Menghapus data NoAssy yang memiliki id terkait dengan Quantity yang akan dihapus
    NoAssy.objects.filter(id__in=no_assy_ids).delete()

    # Menghapus data terkait carline dari Quantity dan Bulan
    Quantity.objects.filter(carline=carline).delete()
    Bulan.objects.filter(carline=carline).delete()
    
    messages.success(request, f"Data untuk carline {carline.name} telah direset.")
    return redirect('sixProductionPlan', name=carline.name)


# Import excel Machine Loading
from django.shortcuts import render, get_object_or_404
import openpyxl
from .models import Carline, MachineLoading, AssyValue

from django.shortcuts import redirect

@login_required()
def machineLoading(request, name):
    carline = get_object_or_404(Carline, name=name)

    ordered_noAssy_headers = []  # Initialize ordered_noAssy_headers

    if request.method == "POST" and 'import' in request.POST:
        excel_files = request.FILES.getlist('file')  # Handle multiple file uploads
        machine_loading_objects = []  # List for bulk creation of MachineLoading
        assy_value_objects = []  # List for bulk creation of AssyValue

        # Ambil semua `noControl` yang sudah ada di database untuk carline yang sama
        existing_noControls = set(MachineLoading.objects.filter(carline=carline).values_list('noControl', flat=True))

        for excel_file in excel_files:
            wb = openpyxl.load_workbook(excel_file)
            sheet = wb.active

            # Extract noAssy headers from column N onwards
            noAssy_headers = []
            col = 14  # Column N is the 14th column
            while sheet.cell(row=1, column=col).value:
                noAssy_headers.append(sheet.cell(row=1, column=col).value)
                col += 1

            # Preserve the order from the Excel file
            ordered_noAssy_headers = noAssy_headers

            # Process each row in the sheet for MachineLoading and AssyValue
            for row in sheet.iter_rows(min_row=2, values_only=True):
                noControl = row[2]

                # Cek apakah noControl sudah ada di database, jika sudah ada, lewati
                if noControl in existing_noControls:
                    continue  # Skip this row if noControl already exists

                # Buat instance MachineLoading baru
                machine_loading = MachineLoading(
                    carline=carline,
                    machine=row[1],
                    noControl=noControl,
                    kind=row[3],
                    size=row[4],
                    twist=row[5],
                    termB=row[6],
                    manB=row[7],
                    accB1=row[8],
                    termA=row[9],
                    manA=row[10],
                    accA1=row[11]
                )
                machine_loading_objects.append(machine_loading)  # Add to bulk create list

                # Process AssyValues for each noAssy
                for index, noAssy in enumerate(noAssy_headers):
                    value = row[13 + index]
                    if value is not None:
                        assy_value = AssyValue(
                            noAssy=noAssy,
                            noControl=machine_loading,  # Link to the MachineLoading instance
                            termB=machine_loading,
                            termA=machine_loading,
                            value=str(value)
                        )
                        assy_value_objects.append(assy_value)  # Add to bulk create list

        # Bulk create MachineLoading and AssyValue objects
        MachineLoading.objects.bulk_create(machine_loading_objects)
        AssyValue.objects.bulk_create(assy_value_objects)

        # Redirect to prevent resubmission if page is refreshed
        return redirect('machineLoading', name=carline.name)

    # Fetch all MachineLoading entries for the selected carline
    machine_loadings = MachineLoading.objects.filter(carline=carline).select_related('carline')

    # Collect all unique noAssy headers from the assy_values
    noAssy_headers = set()
    assy_value_dict = {}
    for loading in machine_loadings:
        assy_values = loading.assy_values.all()
        for assy_value in assy_values:
            noAssy_headers.add(assy_value.noAssy)
            if loading not in assy_value_dict:
                assy_value_dict[loading] = {}
            assy_value_dict[loading][assy_value.noAssy] = assy_value.value

    # If noAssy headers were populated during import, use that order, otherwise sort them
    if not ordered_noAssy_headers:
        ordered_noAssy_headers = sorted(noAssy_headers)

    return render(request, 'machineLoading.html', {
        'carline': carline,
        'machine_loadings': machine_loadings,
        'noAssy_headers': ordered_noAssy_headers,  # Use the ordered headers
        'assy_value_dict': assy_value_dict  # Pass assy values to the template
    })

    
@login_required()
def reset_machineLoading(request, name):
    carline = get_object_or_404(Carline, name=name)

    # Deleting related data from AssyValue first to avoid ForeignKey constraint issues
    machine_loadings = MachineLoading.objects.filter(carline=carline)
    AssyValue.objects.filter(noControl__in=machine_loadings).delete()
    
    # Now delete the MachineLoading entries
    machine_loadings.delete()

    messages.success(request, f"Data untuk carline {carline.name} telah direset.")
    return redirect('machineLoading', name=carline.name)


# CalPart1
from django.db.models import Sum    
from collections import OrderedDict
from .models import Carline, MachineLoading, AssyValue, Quantity, CalculationResult, CalculationResultLoading

@login_required()
def machineLoadingCalculate(request, name):
    carline = get_object_or_404(Carline, name=name)

    # Ambil semua tahun yang tersedia dari Quantity untuk carline ini
    available_years = Quantity.objects.filter(carline=carline).values_list('year', flat=True).distinct().order_by('year')

    # Gunakan tahun terakhir sebagai default (jika ada)
    year = available_years.last() if available_years else None

    # Jika year tidak ditemukan, munculkan pesan
    if not year:
        messages.error(request, "Data Quantity untuk carline ini belum tersedia.")
        return redirect('sixProductionPlan', name=carline.name)

    # Cek apakah data sudah ada di tabel CalculationResultLoading untuk carline dan tahun tertentu
    if CalculationResultLoading.objects.filter(carline=carline, year=year).exists():
        aggregated_results_termB = {}
        aggregated_results_termA = {}
        aggregated_results_combined = {}

        calculation_results_loading = CalculationResultLoading.objects.filter(carline=carline, year=year)

        for result in calculation_results_loading:
            terminal = result.terminal
            month = result.month

            # Agregasi Term B
            if terminal not in aggregated_results_termB:
                aggregated_results_termB[terminal] = {}
            if month not in aggregated_results_termB[terminal]:
                aggregated_results_termB[terminal][month] = 0
            aggregated_results_termB[terminal][month] += result.result

            # Agregasi Term A
            if terminal not in aggregated_results_termA:
                aggregated_results_termA[terminal] = {}
            if month not in aggregated_results_termA[terminal]:
                aggregated_results_termA[terminal][month] = 0
            aggregated_results_termA[terminal][month] += result.result

            # Gabungan
            if terminal not in aggregated_results_combined:
                aggregated_results_combined[terminal] = {}
            if month not in aggregated_results_combined[terminal]:
                aggregated_results_combined[terminal][month] = 0
            aggregated_results_combined[terminal][month] = (
                aggregated_results_termB[terminal][month] +
                aggregated_results_termA[terminal][month]
            )

        def sort_key(item):
            return item if isinstance(item, str) else ""

        aggregated_results_termB = OrderedDict(sorted(aggregated_results_termB.items(), key=lambda x: sort_key(x[0])))
        aggregated_results_termA = OrderedDict(sorted(aggregated_results_termA.items(), key=lambda x: sort_key(x[0])))
        aggregated_results_combined = OrderedDict(sorted(aggregated_results_combined.items(), key=lambda x: sort_key(x[0])))

        return render(request, 'machineLoadingCalculate.html', {
            'carline': carline,
            'result_summary': {},
            'months_order': ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'],
            'aggregated_results_termB': aggregated_results_termB,
            'aggregated_results_termA': aggregated_results_termA,
            'aggregated_results_combined': aggregated_results_combined,
            'year': year,
        })

    CalculationResult.objects.filter(carline=carline, year=year).delete()
    CalculationResultLoading.objects.filter(carline=carline, year=year).delete()

    machine_loadings = MachineLoading.objects.filter(carline=carline)
    result_summary = {}
    months_order = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

    for machine_loading in machine_loadings:
        no_control = machine_loading.noControl
        term_b = machine_loading.termB or '-'
        term_a = machine_loading.termA or '-'

        if no_control not in result_summary:
            result_summary[no_control] = {'termB': term_b, 'termA': term_a, **{month: 0 for month in months_order}}

        assy_values = AssyValue.objects.filter(noControl=machine_loading)

        for assy_value in assy_values:
            quantities = Quantity.objects.filter(noAssy__noAssy=assy_value.noAssy, carline=carline, year=year)

            for quantity in quantities:
                if quantity.carline != carline:
                    continue

                month = quantity.month
                quantity_value = quantity.value

                try:
                    value_assy = int(assy_value.value)
                except ValueError:
                    value_assy = 0

                result = quantity_value * value_assy
                result_summary[no_control][month] += result

                CalculationResult.objects.update_or_create(
                    carline=carline,
                    noControl=machine_loading,
                    termB=machine_loading,
                    termA=machine_loading,
                    month=month,
                    year=year,
                    defaults={'result': result_summary[no_control][month]},
                )

    aggregated_results_termB = {}
    aggregated_results_termA = {}
    aggregated_results_combined = {}

    calculation_results = CalculationResult.objects.filter(carline=carline, year=year)

    for result in calculation_results:
        termB_name = result.termB.termB if result.termB else None
        termA_name = result.termA.termA if result.termA else None
        month = result.month

        if termB_name:
            if termB_name not in aggregated_results_termB:
                aggregated_results_termB[termB_name] = {}
            if month not in aggregated_results_termB[termB_name]:
                aggregated_results_termB[termB_name][month] = 0
            aggregated_results_termB[termB_name][month] += result.result

        if termA_name:
            if termA_name not in aggregated_results_termA:
                aggregated_results_termA[termA_name] = {}
            if month not in aggregated_results_termA[termA_name]:
                aggregated_results_termA[termA_name][month] = 0
            aggregated_results_termA[termA_name][month] += result.result

    # Simpan termB
    for termB_name, months_data in aggregated_results_termB.items():
        for month, result in months_data.items():
            if not CalculationResultLoading.objects.filter(carline=carline, terminal=termB_name, month=month, year=year).exists():
                CalculationResultLoading.objects.create(
                    carline=carline,
                    terminal=termB_name,
                    month=month,
                    year=year,
                    result=result
                )

    # Simpan termA
    for termA_name, months_data in aggregated_results_termA.items():
        for month, result in months_data.items():
            if not CalculationResultLoading.objects.filter(carline=carline, terminal=termA_name, month=month, year=year).exists():
                CalculationResultLoading.objects.create(
                    carline=carline,
                    terminal=termA_name,
                    month=month,
                    year=year,
                    result=result
                )

    # Gabungkan hanya untuk ditampilkan, TIDAK disimpan ke DB
    for term in set(aggregated_results_termB.keys()).union(set(aggregated_results_termA.keys())):
        if term:
            aggregated_results_combined[term] = {}
            for month in set(aggregated_results_termB.get(term, {}).keys()).union(aggregated_results_termA.get(term, {}).keys()):
                combined_result = (
                    aggregated_results_termB.get(term, {}).get(month, 0) +
                    aggregated_results_termA.get(term, {}).get(month, 0)
                )
                aggregated_results_combined[term][month] = combined_result


    def sort_key(item):
        return item if isinstance(item, str) else ""

    aggregated_results_termB = OrderedDict(sorted(aggregated_results_termB.items(), key=lambda x: sort_key(x[0])))
    aggregated_results_termA = OrderedDict(sorted(aggregated_results_termA.items(), key=lambda x: sort_key(x[0])))
    aggregated_results_combined = OrderedDict(sorted(aggregated_results_combined.items(), key=lambda x: sort_key(x[0])))

    return render(request, 'machineLoadingCalculate.html', {
        'carline': carline,
        'result_summary': result_summary,
        'months_order': months_order,
        'aggregated_results_termB': aggregated_results_termB,
        'aggregated_results_termA': aggregated_results_termA,
        'aggregated_results_combined': aggregated_results_combined,
        'year': year,
    })

from django.shortcuts import render
from django.db.models import Sum
from django.db import transaction
from .models import CalculationResultLoading
from django.contrib.auth.decorators import login_required

@login_required()
def requirementPartAllCarline(request):
    try:
        # Ambil data dan agregasi berdasarkan carline, terminal, bulan, dan tahun
        raw_results = CalculationResultLoading.objects.filter(
            terminal__isnull=False,
            terminal__gt='',
            carline__isnull=False
        ).values(
            'carline__name', 'terminal', 'month', 'year' 
        ).annotate(
            total_result=Sum('result')
        ).order_by('carline__name', 'terminal', 'year', 'month')  

        # Susun dictionary: (carline, terminal, year) -> month -> result
        aggregated_results = {}
        for entry in raw_results:
            carline = entry['carline__name']
            terminal = entry['terminal']
            month = entry['month']
            year = entry['year']
            total_result = entry['total_result']

            key = (carline, terminal, year)

            if key not in aggregated_results:
                aggregated_results[key] = {
                    'JAN': "", 'FEB': "", 'MAR': "", 'APR': "",
                    'MAY': "", 'JUN': "", 'JUL': "", 'AUG': "",
                    'SEP': "", 'OCT': "", 'NOV': "", 'DEC': ""
                }

            aggregated_results[key][month] = total_result

        context = {
            'aggregated_results': aggregated_results
        }
        return render(request, 'requirementPartAllCarline.html', context)

    except Exception as e:
        return render(request, 'requirementPartAllCarline.html', {
            'error': f'Terjadi kesalahan: {str(e)}'
        })

         
# Loading Part
import math
from .models import Load_applicator, AggregatedResultByTerminal, TerminalNameMapping, CalculationResultLoading

def process_terminal_mappings():
    load_applicators = Load_applicator.objects.all()
    aggregated_results = AggregatedResultByTerminal.objects.select_related('calculation_result').all()

    for applicator in load_applicators:
        if not applicator.loading or applicator.loading == 0:
            continue

        for aggregated_result in aggregated_results:
            if not aggregated_result.total_result:
                continue

            # Cari calculation_result jika belum ada
            if not aggregated_result.calculation_result:
                related_result = CalculationResultLoading.objects.filter(
                    terminal=aggregated_result.terminal,
                    month=aggregated_result.month
                ).first()
                if related_result:
                    aggregated_result.calculation_result = related_result
                    aggregated_result.save()

            try:
                last_loading = round(aggregated_result.total_result / applicator.loading, 3)
            except ZeroDivisionError:
                last_loading = None

            mapping, created = TerminalNameMapping.objects.get_or_create(
                name=applicator,
                month=aggregated_result,
                defaults={
                    'terminal': aggregated_result,
                    'total_result': aggregated_result,
                    'last_loading': last_loading
                }
            )
            if not created:
                mapping.last_loading = last_loading
                mapping.save()

    terminal_mappings = TerminalNameMapping.objects.select_related(
        'terminal__calculation_result', 'month', 'name'
    ).all()

    terminal_data = {}
    month_order = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                   'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

    for mapping in terminal_mappings:
        if not mapping.terminal or not mapping.month or not mapping.name:
            continue

        terminal_name = getattr(mapping.terminal, 'terminal', None)
        if not terminal_name:
            continue

        month = mapping.month.month.upper()[:3]
        total_result = getattr(mapping.total_result, 'total_result', 0)

        # Ambil carline dari calculation_result jika tersedia
        carline = (
            mapping.terminal.calculation_result.carline.name
            if mapping.terminal.calculation_result and mapping.terminal.calculation_result.carline
            else 'N/A'
        )

        year = (
            mapping.terminal.calculation_result.year
            if mapping.terminal.calculation_result else 'N/A'
        )

        terminal_data.setdefault(carline, {}).setdefault(year, {}).setdefault(month, []).append({
            'name': mapping.name.name,
            'loading': mapping.name.loading,
            'image': mapping.name.image.url if mapping.name.image else None,
            'total_result': total_result,
            'last_loading': mapping.last_loading,
            'terminal': terminal_name  # terminal disertakan di dalam dictionary
        })

    # Urutkan berdasarkan bulan
    for carline in terminal_data:
        for year in terminal_data[carline]:
            sorted_months = dict(sorted(
                terminal_data[carline][year].items(),
                key=lambda x: month_order.index(x[0])
            ))
            terminal_data[carline][year] = sorted_months


    return terminal_data

# Roundup Loading
import math
from .models import Load_applicator, AggregatedResultByTerminal, TerminalNameMapping, LastRoundup, CalculationResultLoading
def process_last_roundup():
    terminal_mappings = TerminalNameMapping.objects.select_related(
        'terminal__calculation_result__carline', 'name', 'month'
    ).all()

    grouped_data = {}
    grouped_data_ceil = {}

    for entry in terminal_mappings:
        if not entry.terminal or not entry.name or not entry.month:
            continue

        terminal_name = getattr(entry.terminal, 'terminal', 'N/A')
        partname = entry.name.name
        month = entry.month.month.upper()[:3]
        last_loading = entry.last_loading
        rounded_loading = math.ceil(last_loading) if last_loading is not None else None

        carline = (
            entry.terminal.calculation_result.carline.name
            if entry.terminal.calculation_result and entry.terminal.calculation_result.carline
            else 'N/A'
        )
        
        year = (
            entry.terminal.calculation_result.year
            if entry.terminal.calculation_result else 'N/A'
        )

        # Siapkan struktur: carline > partname > terminal > month
        grouped_data.setdefault(carline, {}).setdefault(year, {}).setdefault(partname, {}).setdefault(terminal_name, {})[month] = {
            'last_loading': last_loading
        }

        grouped_data_ceil.setdefault(carline, {}).setdefault(year, {}).setdefault(partname, {}).setdefault(terminal_name, {})[month] = {
            'rounded_loading': rounded_loading
        }


        if rounded_loading is not None:
            LastRoundup.objects.update_or_create(
                terminal=entry.terminal,
                name=entry.name,
                month=entry.month,
                defaults={
                    'rounded_loading': str(rounded_loading),
                    'year': year
                }
            )


    return grouped_data, grouped_data_ceil

from django.contrib.auth.decorators import login_required 
from django.shortcuts import render
from .models import Carline, LoadingPartResult, PartDesk
from django.db.models import Q
import math

@login_required
def loadingPart(request):
    terminal_data = process_terminal_mappings()
    grouped_data, grouped_data_ceil = process_last_roundup()
    months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
              "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

    carline_cache = {c.name: c for c in Carline.objects.all()}
    temp_storage = {}

    for carline, years in grouped_data.items():
        for year, parts in years.items():
            for part_name, terminals in parts.items():
                for terminal, month_values in terminals.items():
                    key = (carline, part_name, terminal)
                    temp_storage.setdefault(key, {"last_loading_values": [], "rounded_loading_values": []})

                    # Cari PartDesk berdasarkan partName & applicatorNumber
                    matched_partdesk = PartDesk.objects.filter(
                        partName__partName=part_name,
                        applicatorNumber__applicatorNumber=terminal
                    ).first()

                    for month, value in month_values.items():
                        last_loading = value.get('last_loading')
                        rounded_loading = (
                            grouped_data_ceil
                            .get(carline, {})
                            .get(year, {})
                            .get(part_name, {})
                            .get(terminal, {})
                            .get(month, {})
                            .get('rounded_loading')
                        )

                        if last_loading is not None and rounded_loading is not None:
                            # Simpan nilai asli & pembulatan terpisah
                            temp_storage[key]["last_loading_values"].append(last_loading)
                            temp_storage[key]["rounded_loading_values"].append(rounded_loading)

                            carline_obj = carline_cache[carline]

                            obj, created = LoadingPartResult.objects.get_or_create(
                                carline=carline_obj,
                                part_name=part_name,
                                terminal=terminal,
                                month=month,
                                year=year,
                                defaults={
                                    'last_loading': last_loading,
                                    'rounded_loading': rounded_loading,
                                    'partdesk': matched_partdesk
                                }
                            )

                            if not created:
                                obj.last_loading = last_loading
                                obj.rounded_loading = rounded_loading
                                obj.partdesk = matched_partdesk
                                obj.save()

    # Hitung rata-rata dari last_loading
    for (carline, part_name, terminal), values_dict in temp_storage.items():
        values = values_dict["last_loading_values"]
        if values:
            avg_val = round(sum(values) / len(values), 3)
            avg_ceil = math.ceil(avg_val)
            carline_obj = carline_cache[carline]

            LoadingPartResult.objects.filter(
                carline=carline_obj,
                part_name=part_name,
                terminal=terminal
            ).update(
                average=avg_val,
                average_round=avg_ceil
            )

    # Siapkan hasil untuk template
    all_results = LoadingPartResult.objects.select_related(
        'carline', 'partdesk', 'partdesk__partName', 'partdesk__applicatorNumber'
    )

    loading_results = {}
    for result in all_results:
        carline_name = result.carline.name
        year = result.year
        part_name = result.part_name
        terminal = result.terminal

        loading_results \
            .setdefault(carline_name, {}) \
            .setdefault(year, {}) \
            .setdefault(part_name, {})[terminal] = {
                "average": result.average,
                "average_round": result.average_round,
                "partdesk": result.partdesk,
            }

    context = {
        "terminal_data": terminal_data,
        "grouped_data": grouped_data,
        "grouped_data_ceil": grouped_data_ceil,
        "months": months,
        "loading_results": loading_results,
    }

    return render(request, 'loadingPart.html', context)
