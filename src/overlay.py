# Kombinationsregel (Beispiel)
grid['combined_score'] = (grid['total_abwaerme_mw_GiZ'].fillna(0).clip(-3,3)/3)*0.6 + \
                         (grid['total_waermebedarf_mw_GiZ'].fillna(0).clip(-3,3)/3)*0.4
# oder: binar (1 wenn beide signifikante Hotspots)
grid['combined_bin'] = ((grid['total_abwaerme_mw_GiZ']>1.96) & (grid['total_waermebedarf_mw_GiZ']>1.96)).astype(int)
