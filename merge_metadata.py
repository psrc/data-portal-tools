from form_results import FormResults

f_res = FormResults('data_sets_luv.xlsx',  #'PSRC Metadata Collection Form.xlsx',
                    in_sheet_name='data_sets',
                    # in_file_dir=r'Y:\Data-Portal\Metadata')
                    in_file_dir=r'C:\Users\cpeak\Repos\data-portal-tools\meta_workspace')
f_res.integrate_fields()