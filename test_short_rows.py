"""
Test script to verify short-row calculations.

Short-row math (count, split adjustment) now lives entirely in
Sweater._compute_initial_split_and_short_rows() / helpers.calculate_short_rows()
(see CLAUDE.md). CastOnPlan is just a data holder for whatever split/
short_row_count Sweater.build() precomputed and passed in, so these tests
drive everything through Sweater(...).build() rather than constructing
CastOnPlan directly.

neck_sts_override pins the cast-on to an exact stitch count (100 here),
sidestepping NECK_SIZES/rounding so the numbers below are reproducible
regardless of size-table changes.
"""

from .raglan import Sweater


def test_xs_with_short_rows():
    """Short rows should bring front and back to the same stitch count."""

    sw = Sweater(
        sts_per_10cm=20,   # 2.0 sts/cm
        rows_per_10cm=28,  # 2.8 rows/cm
        size="XS",
        neck_sts_override=100,
        raglan_lines=4,
        raglan_line_sts=2,
        use_short_rows=True,
        short_row_depth_cm=5.0,
    )
    parts = sw.build()
    co = parts["cast_on"]

    neck_sts = co.neck_sts
    split = co.split_map()
    pairs = co.short_row_count // 2  # short_row_count is individual rows

    print("=== XS SIZE SHORT ROW TEST ===")
    print(f"Cast-on: {neck_sts} sts")
    print(f"Short row rounds (pairs): {pairs}")
    print(f"\nInitial split (at cast-on):")
    print(f"  Back: {split['back']}")
    print(f"  Front: {split['front']}")
    print(f"  Sleeve L: {split['sleeve_L']}")
    print(f"  Sleeve R: {split['sleeve_R']}")
    print(f"  Plus raglan: {sw.raglan_lines * sw.raglan_line_sts} sts")

    # Final split (after short rows): back and both sleeves grow, front doesn't.
    final_back = split["back"] + 2 * pairs
    final_front = split["front"]
    final_sleeve_l = split["sleeve_L"] + pairs
    final_sleeve_r = split["sleeve_R"] + pairs

    print(f"\nFinal split (after {pairs} short row rounds):")
    print(f"  Back: {final_back}")
    print(f"  Front: {final_front}")
    print(f"  Sleeve L: {final_sleeve_l}")
    print(f"  Sleeve R: {final_sleeve_r}")

    assert neck_sts == 100, f"Cast-on should be 100, got {neck_sts}"
    print("  ✓ Cast-on matches target (100 sts)")

    assert final_front == final_back, "Front and back should be equal after short rows!"
    print("  ✓ Front equals back after short rows")

    print("\n✓ All tests passed!")


def test_no_short_rows():
    """With no short rows, the initial 3:3:2:2-style split keeps front == back."""

    sw = Sweater(
        sts_per_10cm=20,
        rows_per_10cm=28,
        size="XS",
        neck_sts_override=100,
        raglan_lines=4,
        raglan_line_sts=2,
        use_short_rows=False,
    )
    parts = sw.build()
    co = parts["cast_on"]

    neck_sts = co.neck_sts
    split = co.split_map()

    print("\n=== NO SHORT ROWS TEST ===")
    print(f"Cast-on: {neck_sts} sts")
    print(f"Split:")
    print(f"  Back: {split['back']}")
    print(f"  Front: {split['front']}")
    print(f"  Sleeve L: {split['sleeve_L']}")
    print(f"  Sleeve R: {split['sleeve_R']}")

    assert co.short_row_count == 0, "No short rows requested, so count should be 0"
    assert split["front"] == split["back"], "Front should equal back with no short rows"
    print("\n✓ Test passed!")


if __name__ == "__main__":
    test_xs_with_short_rows()
    test_no_short_rows()
