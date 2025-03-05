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
                files = request.FILES.getlist('file')  # Ambil beberapa file dari request
                sheet_name = form.cleaned_data.get('sheet_name')

                for file in files:  # Loop melalui setiap file yang diunggah
                    try:
                        if sheet_name:
                            df = pd.read_excel(file, sheet_name=sheet_name, header=[12, 13])
                        else:
                            df = pd.read_excel(file, header=[12, 13])
                            
                        months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
                        prod_columns = [(month, 'Prod') for month in months if (month, 'Prod') in df.columns]

                        if not prod_columns:
                            messages.error(request, "Tidak ada kolom 'Prod' yang ditemukan di bawah kolom bulan.")
                            return redirect('sixProductionPlan', name=carline.name)

                        prod_values = []
                        for month, prod_col in prod_columns:
                            prod_values.append(df[(month, 'Prod')].tolist())

                        combined_prod_values = sum(prod_values, [])

                        headers = df.columns.tolist()
                        month_map = {
                            'JAN': 'JAN', 'FEB': 'FEB', 'MAR': 'MAR', 'APR': 'APR',
                            'MAY': 'MAY', 'JUN': 'JUN', 'JUL': 'JUL', 'AUG': 'AUG',
                            'SEP': 'SEP', 'OCT': 'OCT', 'NOV': 'NOV', 'DEC': 'DEC'
                        }

                        no_assy_column_index = 4

                        for index, row in df.iterrows():
                            no_assy_value = row.iloc[no_assy_column_index] if no_assy_column_index < len(row) else None
                            if no_assy_value is None or pd.isna(no_assy_value) or str(no_assy_value).strip() == "":
                                messages.error(request, f"Empty or missing noAssy at row {index}. Stopping import.")
                                break

                            no_assy, created = NoAssy.objects.get_or_create(noAssy=no_assy_value)

                            bulan_data = {month: None for month in month_map.keys()}

                            for (month, prod_col) in prod_columns:
                                value = row[(month, 'Prod')]
                                if pd.notna(value) and str(value).strip():
                                    try:
                                        bulan_data[month_map[month]] = int(value)
                                    except ValueError:
                                        bulan_data[month_map[month]] = None

                            bulan, created = Bulan.objects.get_or_create(carline=carline, **bulan_data)

                            for month in bulan_data.keys():
                                value = bulan_data[month]
                                if value is not None:
                                    quantity_exists = Quantity.objects.filter(
                                        bulan=bulan, noAssy=no_assy, month=month
                                    ).exists()
                                    if not quantity_exists:
                                        Quantity.objects.create(
                                            bulan=bulan, noAssy=no_assy, month=month, value=value, carline=carline
                                        )

                    except Exception as e:
                        messages.error(request, f"Gagal membaca file Excel: {e}")

            return redirect('sixProductionPlan', name=carline.name)

        elif 'reset' in request.POST:
            Bulan.objects.filter(carline=carline).delete()
            Quantity.objects.filter(carline=carline).delete()  # Menghapus Quantity yang terkait dengan carline
            NoAssy.objects.filter(id__in=Quantity.objects.filter(carline=carline).values_list('noAssy_id', flat=True)).delete()
            messages.success(request, f"Data untuk carline {carline.name} telah direset.")
            return redirect('sixProductionPlan', name=carline.name)

    bulan_list = Bulan.objects.filter(carline=carline)
    months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
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
    # Get carline based on name
    carline = get_object_or_404(Carline, name=name)

    # Cek apakah data sudah ada di tabel CalculationResultLoading
    if CalculationResultLoading.objects.filter(carline=carline).exists():
        # Jika data sudah ada, langsung ambil dari database
        aggregated_results_termB = {}
        aggregated_results_termA = {}
        aggregated_results_combined = {}

        # Ambil semua hasil perhitungan dari CalculationResultLoading
        calculation_results_loading = CalculationResultLoading.objects.filter(carline=carline)

        for result in calculation_results_loading:
            terminal = result.terminal
            month = result.month

            # Agregasi hasil untuk Term B
            if terminal not in aggregated_results_termB:
                aggregated_results_termB[terminal] = {}
            if month not in aggregated_results_termB[terminal]:
                aggregated_results_termB[terminal][month] = 0
            aggregated_results_termB[terminal][month] += result.result

            # Agregasi hasil untuk Term A
            if terminal not in aggregated_results_termA:
                aggregated_results_termA[terminal] = {}
            if month not in aggregated_results_termA[terminal]:
                aggregated_results_termA[terminal][month] = 0
            aggregated_results_termA[terminal][month] += result.result

            # Menggabungkan Term B dan Term A
            if terminal not in aggregated_results_combined:
                aggregated_results_combined[terminal] = {}
            if month not in aggregated_results_combined[terminal]:
                aggregated_results_combined[terminal][month] = 0
            aggregated_results_combined[terminal][month] = aggregated_results_termB[terminal][month] + aggregated_results_termA[terminal][month]

        # Mengurutkan hasil agar lebih mudah dibaca
        def sort_key(item):
            return item if isinstance(item, str) else ""

        aggregated_results_termB = OrderedDict(sorted(aggregated_results_termB.items(), key=lambda x: sort_key(x[0])))
        aggregated_results_termA = OrderedDict(sorted(aggregated_results_termA.items(), key=lambda x: sort_key(x[0])))
        aggregated_results_combined = OrderedDict(sorted(aggregated_results_combined.items(), key=lambda x: sort_key(x[0])))

        # Render hasil tanpa perhitungan ulang
        return render(request, 'machineLoadingCalculate.html', {
            'carline': carline,
            'result_summary': {},  # Kosongkan result_summary karena kita tidak menghitung ulang
            'months_order': ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'],
            'aggregated_results_termB': aggregated_results_termB,
            'aggregated_results_termA': aggregated_results_termA,
            'aggregated_results_combined': aggregated_results_combined,
        })

    # Jika data belum ada, lakukan perhitungan ulang seperti biasa
    CalculationResult.objects.filter(carline=carline).delete()
    CalculationResultLoading.objects.filter(carline=carline).delete()

    # Get all MachineLoading records related to this carline
    machine_loadings = MachineLoading.objects.filter(carline=carline)

    # Dictionary to store the sum results based on noControl and month
    result_summary = {}

    # List of months in the desired order
    months_order = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

    # Iterate over each MachineLoading
    for machine_loading in machine_loadings:
        no_control = machine_loading.noControl
        term_b = machine_loading.termB or '-'
        term_a = machine_loading.termA or '-'

        # Initialize result_summary for each noControl if not already done
        if no_control not in result_summary:
            result_summary[no_control] = {'termB': term_b, 'termA': term_a, **{month: 0 for month in months_order}}

        # Get all AssyValue related to this noControl
        assy_values = AssyValue.objects.filter(noControl=machine_loading)

        for assy_value in assy_values:
            # Get the corresponding quantities based on noAssy and carline
            quantities = Quantity.objects.filter(noAssy__noAssy=assy_value.noAssy, carline=carline)

            for quantity in quantities:
                # Validasi bahwa carline dari Quantity cocok dengan carline yang diproses
                if quantity.carline != carline:
                    continue  # Jika tidak cocok, lewati perhitungan untuk record ini

                month = quantity.month
                quantity_value = quantity.value

                # Multiply the value from AssyValue with the Quantity value
                try:
                    value_assy = int(assy_value.value)
                except ValueError:
                    value_assy = 0

                result = quantity_value * value_assy

                # Add the result to the correct month in result_summary
                result_summary[no_control][month] += result

                # Save or update the result in CalculationResult
                CalculationResult.objects.update_or_create(
                    carline=carline,
                    noControl=machine_loading,
                    termB=machine_loading, 
                    termA=machine_loading, 
                    month=month,
                    defaults={'result': result_summary[no_control][month]},
                )

    # Start aggregating results
    aggregated_results_termB = {}
    aggregated_results_termA = {}
    aggregated_results_combined = {}

    calculation_results = CalculationResult.objects.filter(carline=carline)

    for result in calculation_results:
        termB_name = result.termB.termB if result.termB else None
        termA_name = result.termA.termA if result.termA else None
        month = result.month

        # Skip processing if termB_name or termA_name is None
        if termB_name:
            # Agregasi untuk Term B
            if termB_name not in aggregated_results_termB:
                aggregated_results_termB[termB_name] = {}
            if month not in aggregated_results_termB[termB_name]:
                aggregated_results_termB[termB_name][month] = 0
            aggregated_results_termB[termB_name][month] += result.result

        if termA_name:
            # Agregasi untuk Term A
            if termA_name not in aggregated_results_termA:
                aggregated_results_termA[termA_name] = {}
            if month not in aggregated_results_termA[termA_name]:
                aggregated_results_termA[termA_name][month] = 0
            aggregated_results_termA[termA_name][month] += result.result

    # Menggabungkan Term A dan Term B
    for term in set(aggregated_results_termB.keys()).union(set(aggregated_results_termA.keys())):
        if term:
            aggregated_results_combined[term] = {}

            for month in set(aggregated_results_termB.get(term, {}).keys()).union(set(aggregated_results_termA.get(term, {}).keys())):
                combined_result = aggregated_results_termB.get(term, {}).get(month, 0) + aggregated_results_termA.get(term, {}).get(month, 0)
                aggregated_results_combined[term][month] = combined_result

                # Pengecekan apakah data sudah ada di tabel CalculationResultLoading
                if not CalculationResultLoading.objects.filter(carline=carline, terminal=term, month=month).exists():
                    # Jika belum ada, simpan data ke tabel CalculationResultLoading
                    if term and term.strip():  # Memastikan term tidak kosong
                        CalculationResultLoading.objects.create(
                            carline=carline,
                            terminal=term,
                            month=month,
                            result=combined_result
                        )

    # Mengurutkan hasil agar lebih mudah dibaca
    def sort_key(item):
        return item if isinstance(item, str) else ""

    aggregated_results_termB = OrderedDict(sorted(aggregated_results_termB.items(), key=lambda x: sort_key(x[0])))
    aggregated_results_termA = OrderedDict(sorted(aggregated_results_termA.items(), key=lambda x: sort_key(x[0])))
    aggregated_results_combined = OrderedDict(sorted(aggregated_results_combined.items(), key=lambda x: sort_key(x[0])))

    # Render results
    return render(request, 'machineLoadingCalculate.html', {
        'carline': carline,
        'result_summary': result_summary,
        'months_order': months_order,
        'aggregated_results_termB': aggregated_results_termB,
        'aggregated_results_termA': aggregated_results_termA,
        'aggregated_results_combined': aggregated_results_combined,
    })


# CARLINE - MachineLoading Fiture - SUM ALL CARLINE

from django.shortcuts import render
from django.db.models import Sum
from django.db import transaction
from .models import CalculationResultLoading, AggregatedResultByTerminal

@login_required()
def requirementPartAllCarline(request):
    try:
        # Memastikan model CalculationResultLoading memiliki field 'terminal', 'month', dan 'result'
        calculation_fields = [field.name for field in CalculationResultLoading._meta.get_fields()]
        
        if 'terminal' in calculation_fields and 'month' in calculation_fields and 'result' in calculation_fields:
            # Mengambil data dari model CalculationResultLoading
            raw_results = CalculationResultLoading.objects.filter(
                terminal__isnull=False,
                terminal__gt=''  # Mengabaikan terminal yang kosong
            ).values('terminal', 'month').annotate(
                total_result=Sum('result')
            ).order_by('terminal', 'month')

            with transaction.atomic():
                # Update atau buat entri baru di AggregatedResultByTerminal
                for entry in raw_results:
                    terminal = entry['terminal']
                    month = entry['month']
                    total_result = entry['total_result']

                    # Update or create data di AggregatedResultByTerminal
                    AggregatedResultByTerminal.objects.update_or_create(
                        terminal=terminal,
                        month=month,
                        defaults={'total_result': total_result}
                    )

            # Mengatur dictionary untuk ditampilkan di template
            aggregated_results = {}
            for entry in raw_results:
                terminal = entry['terminal']
                month = entry['month']
                total_result = entry['total_result']

                # Struktur untuk template
                if terminal not in aggregated_results:
                    aggregated_results[terminal] = {
                        'JAN': "", 'FEB': "", 'MAR': "", 'APR': "",
                        'MAY': "", 'JUN': "", 'JUL': "", 'AUG': "",
                        'SEP': "", 'OCT': "", 'NOV': "", 'DEC': ""
                    }
                aggregated_results[terminal][month] = total_result

            context = {
                'aggregated_results': aggregated_results,  # Tabel untuk template
            }
        else:
            context = {
                'error': "Field 'terminal', 'month', atau 'result' tidak ditemukan di model CalculationResultLoading."
            }

        return render(request, 'requirementPartAllCarline.html', context)

    except Exception as e:
        context = {
            'error': f"Terjadi kesalahan saat mengambil data: {str(e)}"
        }
        return render(request, 'requirementPartAllCarline.html', context)



from .models import Load_applicator, AggregatedResultByTerminal, TerminalNameMapping, LastRoundup, PartDesk, ApplicatorPartAvarage
import math
from django.shortcuts import render

@login_required()
def loadingPart(request):
    # Part 1: Terminal Name Mapping Logic
    load_applicators = Load_applicator.objects.all()
    aggregated_results = AggregatedResultByTerminal.objects.all()

    # Loop and save data for TerminalNameMapping
    for applicator in load_applicators:
        for aggregated_result in aggregated_results:
            last_loading = aggregated_result.total_result / applicator.loading
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

    # Retrieve TerminalNameMapping data
    terminal_mappings = TerminalNameMapping.objects.select_related('terminal', 'month', 'name').all()

    # Prepare terminal data for the template
    terminal_data = {}
    month_order = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

    for mapping in terminal_mappings:
        terminal_name = mapping.terminal.terminal
        month = mapping.month.month.upper()[:3]  # First three letters of the month
        total_result = mapping.total_result.total_result

        if terminal_name not in terminal_data:
            terminal_data[terminal_name] = {}

        if month not in terminal_data[terminal_name]:
            terminal_data[terminal_name][month] = []

        terminal_data[terminal_name][month].append({
            'name': mapping.name.name,
            'loading': mapping.name.loading,
            'image': mapping.name.image.url if mapping.name.image else None,
            'total_result': total_result,
            'last_loading': mapping.last_loading
        })

    # Sort months for terminal data
    for terminal in terminal_data:
        sorted_months = dict(sorted(terminal_data[terminal].items(), key=lambda x: month_order.index(x[0])))
        terminal_data[terminal] = sorted_months

    # Group data for LastRoundup
    grouped_data = {}
    grouped_data_ceil = {}

    for entry in terminal_mappings:
        applicator = entry.terminal.terminal  # Applicator Number
        partname = entry.name.name  # Partname
        
        if applicator not in grouped_data:
            grouped_data[applicator] = {}
            grouped_data_ceil[applicator] = {}

        if partname not in grouped_data[applicator]:
            grouped_data[applicator][partname] = {month: None for month in month_order}
            grouped_data_ceil[applicator][partname] = {month: None for month in month_order}

        # Fill the corresponding month with the last_loading value
        month = entry.month.month.upper()[:3]  # First three letters of the month
        last_loading = entry.last_loading
        rounded_loading = math.ceil(last_loading) if last_loading is not None else None

        # Store the last_loading in grouped_data
        grouped_data[applicator][partname][month] = last_loading

        # Store the rounded value in grouped_data_ceil and save to LastRoundup table
        grouped_data_ceil[applicator][partname][month] = rounded_loading

        if rounded_loading is not None:
            # Simpan sebagai string agar tidak ada koma
            rounded_loading_str = str(rounded_loading)

            # Save rounded values in LastRoundup
            LastRoundup.objects.update_or_create(
                terminal=entry.terminal,
                name=entry.name,
                month=entry.month,
                defaults={'rounded_loading': rounded_loading_str}
            )


    # Part 2: Combined Data View Logic
    # Clear old data from ApplicatorPartAvarage
    ApplicatorPartAvarage.objects.all().delete()

    # Fetch data from LastRoundup and PartDesk
    last_roundups = LastRoundup.objects.all().order_by('terminal__terminal', 'name__name', 'month__month')
    part_desks = PartDesk.objects.all().order_by('applicatorNumber__applicatorNumber', 'partName__partName')

    # Dictionary to store combined results
    combined_results = {}

    # Loop through data in LastRoundup and PartDesk
    for last_roundup in last_roundups:
        for part_desk in part_desks:
            # If terminal and applicatorNumber match
            if last_roundup.terminal.terminal == part_desk.applicatorNumber.applicatorNumber:
                # If name matches
                if last_roundup.name.name == part_desk.partName.partName:
                    key = (part_desk.applicatorNumber.applicatorNumber, part_desk.partName.partName)

                    # Initialize dictionary for months if it doesn't exist
                    if key not in combined_results:
                        combined_results[key] = {
                            'terminal': last_roundup.terminal.terminal,
                            'name': last_roundup.name.name,
                            'part_number': part_desk.partNumber,
                            'part_code': part_desk.partCode,
                            'level': part_desk.level,
                            'marking': part_desk.marking,
                            'months': {month: None for month in month_order}
                        }

                    # Assign the rounded_loading to the correct month
                    month = last_roundup.month.month.upper()
                    if month in combined_results[key]['months']:
                        combined_results[key]['months'][month] = str(last_roundup.rounded_loading)

    # Calculate the average and save to ApplicatorPartAvarage model
    for key, data in combined_results.items():
        months_data = data['months']
        
        # Calculate average as float
        valid_values = [float(value) for value in months_data.values() if value is not None]
        average = sum(valid_values) / len(valid_values) if valid_values else 0
        data['average'] = round(average, 2)

        # Convert numeric values to string without decimal points for months
        def convert_to_str(value):
            try:
                if value is None or value == "":  # If the value is None or empty string, return "-"
                    return "-"
                # Handle conversion of numeric values to int if possible, otherwise leave as string
                float_val = float(value)
                int_val = int(float_val)  # Safely convert float to int
                return str(int_val)  # Convert int to string
            except (ValueError, TypeError):
                # If it's not a numeric value (like '-') or can't be converted, just return it as a string
                return str(value)



        # Save combined data into ApplicatorPartAvarage
        ApplicatorPartAvarage.objects.update_or_create(
            terminal=data['terminal'],
            name=data['name'],
            part_number=data['part_number'],
            defaults={
                'part_code': data['part_code'],
                'level': data['level'],
                'marking': data['marking'],
                'jan': convert_to_str(data['months'].get('JAN', None)),
                'feb': convert_to_str(data['months'].get('FEB', None)),
                'mar': convert_to_str(data['months'].get('MAR', None)),
                'apr': convert_to_str(data['months'].get('APR', None)),
                'may': convert_to_str(data['months'].get('MAY', None)),
                'jun': convert_to_str(data['months'].get('JUN', None)),
                'jul': convert_to_str(data['months'].get('JUL', None)),
                'aug': convert_to_str(data['months'].get('AUG', None)),
                'sep': convert_to_str(data['months'].get('SEP', None)),
                'oct': convert_to_str(data['months'].get('OCT', None)),
                'nov': convert_to_str(data['months'].get('NOV', None)),
                'dec': convert_to_str(data['months'].get('DEC', None)),
                'average': data['average']  # Average stays as float
            }
        )

    # Combine data from both parts
    context = {
        'terminal_data': terminal_data,
        'grouped_data': grouped_data,
        'grouped_data_ceil': grouped_data_ceil,
        'combined_results': combined_results
    }

    return render(request, 'loadingPart.html', context)

# views.py
import openpyxl
from django.http import HttpResponse
from .models import ApplicatorPartAvarage
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
import datetime  # Import datetime untuk mendapatkan tanggal hari ini
from datetime import datetime

@login_required()
def export_dashboard(request):
    # Buat workbook dan worksheet baru
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = "Machine Loading Part"

    # Merge cells untuk judul "Machine Loading Part" di kolom D-J (kolom ke-4 sampai ke-10), baris ke-3
    worksheet.merge_cells('D3:J3')
    worksheet["D3"] = "MACHINE LOADING PART"
    worksheet["D3"].font = Font(size=20, bold=True)  # Set font size dan bold
    worksheet["D3"].alignment = Alignment(horizontal="center", vertical="center")  # Rata tengah
    
    # Merge cells for "CONFIDENTIAL" text
    worksheet.merge_cells('N3:Q3')
    worksheet["N3"] = "CONFIDENTIAL"
    worksheet["N3"].font = Font(size=16, bold=True, color="FF0000")  # Set font size and bold with red color
    worksheet["N3"].alignment = Alignment(horizontal="center", vertical="center")  # Center align the text

    # Mendapatkan tanggal dan waktu saat ini
    now = datetime.now()

    # Mengisi waktu di B5 dengan format HH:MM:SS
    worksheet["A5"] = "Time:"
    worksheet["B5"] = now.strftime('%H:%M:%S')  # Format jam:menit:detik
    worksheet["B5"].font = Font(size=11)  # Set font size untuk waktu
    worksheet["B5"].alignment = Alignment(horizontal="left")  # Rata kiri untuk waktu

    # Mengisi tanggal di B6 dengan format dd-mm-yyyy
    worksheet["A6"] = "Date:"
    worksheet["B6"] = now.strftime('%d-%m-%Y')  # Format hari-bulan-tahun
    worksheet["B6"].font = Font(size=11)  # Set font size untuk tanggal
    worksheet["B6"].alignment = Alignment(horizontal="left")  # Rata kiri untuk tanggal

    
    # Define the red border
    red_border = Border(
        left=Side(border_style="thick", color="FF0000"),
        right=Side(border_style="thick", color="FF0000"),
        top=Side(border_style="thick", color="FF0000"),
        bottom=Side(border_style="thick", color="FF0000")
    )

    # Apply the red border to all cells within the merged range (N3:Q3)
    for row in worksheet.iter_rows(min_row=3, max_row=3, min_col=14, max_col=17):  # Columns N-Q correspond to 14-17
        for cell in row:
            cell.border = red_border

    # Tambahkan header kolom di baris ke-7
    headers = ['Machine Number', 'Part Name', 'Part Number', 'Level / Marking', 'Category', 
               'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC', 'Average']

    # Append empty rows to reach row 7
    for _ in range(1):  # Add 6 empty rows before row 7
        worksheet.append([None] * len(headers))

    # Tambahkan header di baris ke-7
    worksheet.append(headers)

    # Set font bold untuk header dan warna background
    header_fill = PatternFill(start_color="DCE6F1", end_color="DCE6F1", fill_type="solid") 
    for col_num, header in enumerate(headers, 1):
        cell = worksheet.cell(row=8, column=col_num)  # Set header on row 7
        cell.font = Font(bold=True)
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")  # Rata tengah header

    # Mapping kolom ke index
    column_mapping = {
        'Machine Number': 0,
        'Part Name': 1,
        'Part Number': 2,
        'Level / Marking': 3,
        'Category': 4,
        'JAN': 5,
        'FEB': 6,
        'MAR': 7,
        'APR': 8,
        'MAY': 9,
        'JUN': 10,
        'JUL': 11,
        'AUG': 12,
        'SEP': 13,
        'OCT': 14,
        'NOV': 15,
        'DEC': 16,
        'Average': 17
    }

    # Border setup
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # Ambil data dari database
    items = ApplicatorPartAvarage.objects.all()

    # Tambahkan data ke worksheet mulai dari baris ke-8
    for item in items:
        row = [None] * len(headers)  # Creating a list with the same length as headers

        # Fill data, using "-" if the value is empty or None
        row[column_mapping['Machine Number']] = str(item.terminal) if item.terminal else "-"
        row[column_mapping['Part Name']] = str(item.name) if item.name else "-"
        row[column_mapping['Part Number']] = f"{item.part_number} {item.part_code}" if item.part_code else str(item.part_number) if item.part_number else "-"
        row[column_mapping['Level / Marking']] = f"{item.level} {item.marking}" if item.marking else str(item.level) if item.level else "-"
        row[column_mapping['Category']] = "Applicator"  # Assuming this is blank, using "-" directly
        row[column_mapping['JAN']] = str(item.jan) if item.jan else "-"
        row[column_mapping['FEB']] = str(item.feb) if item.feb else "-"
        row[column_mapping['MAR']] = str(item.mar) if item.mar else "-"
        row[column_mapping['APR']] = str(item.apr) if item.apr else "-"
        row[column_mapping['MAY']] = str(item.may) if item.may else "-"
        row[column_mapping['JUN']] = str(item.jun) if item.jun else "-"
        row[column_mapping['JUL']] = str(item.jul) if item.jul else "-"
        row[column_mapping['AUG']] = str(item.aug) if item.aug else "-"
        row[column_mapping['SEP']] = str(item.sep) if item.sep else "-"
        row[column_mapping['OCT']] = str(item.oct) if item.oct else "-"
        row[column_mapping['NOV']] = str(item.nov) if item.nov else "-"
        row[column_mapping['DEC']] = str(item.nov) if item.nov else "-"
        row[column_mapping['Average']] = "{:.2f}".format(item.average) if item.average is not None else "-"

        worksheet.append(row)

    # Terapkan border untuk semua sel yang terisi mulai dari baris ke-7
    for row in worksheet.iter_rows(min_row=8, max_row=worksheet.max_row, min_col=1, max_col=len(headers)):
        for cell in row:
            cell.border = thin_border

    # Atur lebar kolom berdasarkan isi
    for col in worksheet.columns:
        max_length = 0
        col_letter = col[0].column_letter  # Mendapatkan huruf kolom
        for cell in col:
            try:  # Tangani sel yang kosong
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except:
                pass
        adjusted_width = (max_length + 2)
        worksheet.column_dimensions[col_letter].width = adjusted_width

    # Simpan file Excel ke dalam HttpResponse
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=Machine_Loading_Part.xlsx'
    workbook.save(response)

    return response

# untuk menghapus semua isi database
from django.shortcuts import redirect
from .models import Item, ExcelFile, Machine, SealUnit, ApplicatorPart, PartDesk, PartName, Carline, Bulan, NoAssy, Quantity, MachineLoading, AssyValue, CalculationResult, CalculationResultLoading, Load_applicator, AggregatedResultByTerminal, TerminalNameMapping, LastRoundup, ViewsCalculateLoad, CombinedModel, ApplicatorPartAvarage

@login_required()
def delete_all_data(request):
    # Hapus semua data dari model-model yang diinginkan
    Item.objects.all().delete()
    ExcelFile.objects.all().delete()
    Machine.objects.all().delete()
    SealUnit.objects.all().delete()
    ApplicatorPart.objects.all().delete()
    PartDesk.objects.all().delete()
    PartName.objects.all().delete()
    Carline.objects.all().delete()
    Bulan.objects.all().delete()
    NoAssy.objects.all().delete()
    Quantity.objects.all().delete()
    MachineLoading.objects.all().delete()
    AssyValue.objects.all().delete()
    CalculationResult.objects.all().delete()
    CalculationResultLoading.objects.all().delete()
    Load_applicator.objects.all().delete()
    AggregatedResultByTerminal.objects.all().delete()
    TerminalNameMapping.objects.all().delete()
    LastRoundup.objects.all().delete()
    ViewsCalculateLoad.objects.all().delete()
    CombinedModel.objects.all().delete()
    ApplicatorPartAvarage.objects.all().delete()
    
    # Redirect setelah penghapusan selesai, misalnya kembali ke halaman utama
    return redirect('dashboard')  # Ganti 'home' dengan nama URL tujuan
