# test.py
# from sweater import Sweater

# --- basic test ---
# 22 sts / 18 rows per 10 cm, size M, 1x1 ribbing (rib_pref = 1)
# sweater = Sweater(22, 18, "M", 1)

# Print your generated pattern
# print(sweater.render_text()) 


# test_sweater.py
from .raglan import Sweater
from .caston import CastOnPlan

def test_basic_no_short_rows():
    sw = Sweater(
        sts_per_10cm=22,
        rows_per_10cm=30,
        size="M",
    )
    print("=== NO SHORT ROWS ===")
    print(sw.render_text())
    print()

def test_with_short_rows():
    sw = Sweater(
        sts_per_10cm=22,
        rows_per_10cm=30,
        size="M",
        use_short_rows=True,
        short_row_depth_cm=5.0,
    )
    print("=== WITH SHORT ROWS ===")
    print(sw.render_text())
    print()

def compare_splits():
    print("=== SPLIT COMPARISON ===")

    # base split (no SR adjustments)
    co_base = CastOnPlan(
        size="M",
        gauge_sts_per_cm=22 / 10,
        rib_multiple=2,
        raglan_lines=4,
        raglan_line_sts=2,
        gauge_rows_per_cm=30 / 10,
        use_short_rows=False,
        short_row_depth_cm=0.0,
    )
    base_split = co_base.split_map()

    # adjusted split (with SR + raglan incs)
    co_sr = CastOnPlan(
        size="M",
        gauge_sts_per_cm=22 / 10,
        rib_multiple=2,
        raglan_lines=4,
        raglan_line_sts=2,
        gauge_rows_per_cm=30 / 10,
        use_short_rows=True,
        short_row_depth_cm=4.0,
    )
    sr_split = co_sr.split_map()

    print("Base split (no SR):      ", base_split)
    print("SR-adjusted split (Short rows:   ", sr_split)

if __name__ == "__main__":
    test_basic_no_short_rows()
    test_with_short_rows()
    compare_splits()
