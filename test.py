# test.py
# from sweater import Sweater

# --- basic test ---
# 22 sts / 18 rows per 10 cm, size M, 1x1 ribbing (rib_pref = 1)
# sweater = Sweater(22, 18, "M", 1)

# Print your generated pattern
# print(sweater.render_text())


# test_sweater.py
from .raglan import Sweater


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
    """
    Compare splits with and without short rows.

    With the new architecture, orchestration happens in Sweater.build(),
    so we use Sweater to get the computed CastOnPlan.
    """
    print("=== SPLIT COMPARISON ===")

    # Without short rows
    sw_no_sr = Sweater(
        sts_per_10cm=22,
        rows_per_10cm=30,
        size="M",
        use_short_rows=False,
    )
    parts_no_sr = sw_no_sr.build()
    co_no_sr = parts_no_sr["cast_on"]
    base_split = co_no_sr.split_map()

    # With short rows
    sw_sr = Sweater(
        sts_per_10cm=22,
        rows_per_10cm=30,
        size="M",
        use_short_rows=True,
        short_row_depth_cm=4.0,
    )
    parts_sr = sw_sr.build()
    co_sr = parts_sr["cast_on"]
    sr_split = co_sr.split_map()

    print("Base split (no SR):       ", base_split)
    print(f"SR-adjusted split:        ", sr_split)
    print(f"Short row count:          {co_sr.short_row_count} individual rows ({co_sr.short_row_count // 2} pairs)")


def write_sample_output():
    """Write all test output to sample_output.txt for easy viewing."""
    import io
    import sys
    from pathlib import Path

    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()

    test_basic_no_short_rows()
    test_with_short_rows()
    compare_splits()

    # Restore stdout and get captured output
    sys.stdout = old_stdout
    output = buffer.getvalue()

    # Print to console as well
    print(output)

    # Write to file
    output_path = Path(__file__).parent / "sample_output.txt"
    output_path.write_text(output)
    print(f"\n[Output written to {output_path}]")


if __name__ == "__main__":
    write_sample_output()
