NEURON user_data/ � manually maintained data files

pm_kusum.xlsx     : PM-KUSUM_A Component-A state-wise data
                    Columns: State_Name | Total_Sanction_MW | Total_Installed_MW
                    Update this file with latest MNRE data as needed.
pm_kusum.xlsx     : PM-KUSUM_B Component-B state-wise data
                    Columns: State_Name | Total_Sanction_Nos. | Total_Installed_Nos.
                    Update this file with latest MNRE data as needed.
pm_kusum.xlsx     : PM-KUSUM_C Component-C state-wise data
                    Columns: State_Name | Total_Sanction_Nos. | Total_Installed_Nos.
                    Update this file with latest MNRE data as needed.

pm_surya_ghar.xlsx: PM Surya Ghar state-wise data (sheet PM_Surya_Ghar)
                    Columns: State / UT | Applications (No.) | Installations (No.) |
                             Households Covered (No.) | Installation Capacity (MW) |
                             Subsidy Released (Cr)
                    National totals are summed from state rows (any 'Total' row is
                    ignored to avoid double counting). Update with latest MNRE data.

Neuron reads these files on every request (no cache bypass needed).
Just save the file and refresh the dashboard.
