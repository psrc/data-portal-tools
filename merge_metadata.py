from form_results import FormResults

f_res = FormResults('PSRC Metadata Collection Form.xlsx',
    in_file_dir=r'Y:\Data-Portal\Metadata')
f_res.integrate_fields()