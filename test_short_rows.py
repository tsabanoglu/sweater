"""
Test script to verify short row calculations.

Example test case (XS size):
- Gauge: 20 sts x 28 rows = 10 x 10 cm (2.0 sts/cm, 2.8 rows/cm)
- Cast-on: 100 sts total
- 5 short row rounds
- Initial split: Back 22, Front 32, Sleeves 19 each (+ 8 raglan)
- After short rows: Back 32, Front 32, Sleeves 24 each (+ 8 raglan) = 120 sts
"""

from .caston import CastOnPlan

def test_xs_with_short_rows():
    """Test short rows with XS size example."""

    # XS size parameters
    gauge_sts_per_cm = 2.0  # 20 sts / 10 cm
    gauge_rows_per_cm = 2.8  # 28 rows / 10 cm

    # Neck circumference to give 100 st cast-on
    # Working backwards: 100 sts total = neck sts
    neck_cm = 100 / gauge_sts_per_cm  # 50 cm

    # Create CastOnPlan with short rows
    co = CastOnPlan(
        size="XS",
        gauge_sts_per_cm=gauge_sts_per_cm,
        gauge_rows_per_cm=gauge_rows_per_cm,
        rib_multiple=2,
        raglan_lines=4,
        raglan_line_sts=2,
        custom_neck_cm=neck_cm,
        use_short_rows=True,
        short_row_depth_cm=5.0,  # Approximate based on 5 rounds
        guard_sts_before_front_raglan=2,
    )

    # Get results
    neck_sts = co.neck_sts
    split = co.split_map()
    R = co.short_row_rounds()

    print("=== XS SIZE SHORT ROW TEST ===")
    print(f"Cast-on: {neck_sts} sts")
    print(f"Short row rounds: {R}")
    print(f"\nInitial split (at cast-on):")
    print(f"  Back: {split['back']}")
    print(f"  Front: {split['front']}")
    print(f"  Sleeve L: {split['sleeve_L']}")
    print(f"  Sleeve R: {split['sleeve_R']}")
    print(f"  Plus raglan: 8 sts")
    print(f"  Total: {split['back'] + split['front'] + split['sleeve_L'] + split['sleeve_R'] + 8}")

    # Calculate final split (after short rows)
    final_back = split['back'] + 2 * R
    final_front = split['front']  # unchanged
    final_sleeve_l = split['sleeve_L'] + R
    final_sleeve_r = split['sleeve_R'] + R

    print(f"\nFinal split (after {R} short row rounds):")
    print(f"  Back: {final_back}")
    print(f"  Front: {final_front}")
    print(f"  Sleeve L: {final_sleeve_l}")
    print(f"  Sleeve R: {final_sleeve_r}")
    print(f"  Plus raglan: 8 sts")
    print(f"  Total: {final_back + final_front + final_sleeve_l + final_sleeve_r + 8}")

    # Verify key properties
    print(f"\nVerification:")
    print(f"  Front:Back ratio after SR: {final_front}:{final_back} (should be equal)")
    assert final_front == final_back, "Front and back should be equal after short rows!"
    print(f"  ✓ Front equals back")

    assert neck_sts == 100, f"Cast-on should be 100, got {neck_sts}"
    print(f"  ✓ Cast-on matches target (100 sts)")

    print("\n✓ All tests passed!")


def test_no_short_rows():
    """Test that no short rows gives standard split."""

    gauge_sts_per_cm = 2.0
    neck_cm = 50.0  # 100 sts

    co = CastOnPlan(
        size="XS",
        gauge_sts_per_cm=gauge_sts_per_cm,
        gauge_rows_per_cm=2.8,
        rib_multiple=2,
        custom_neck_cm=neck_cm,
        use_short_rows=False,
    )

    neck_sts = co.neck_sts
    split = co.split_map()

    print("\n=== NO SHORT ROWS TEST ===")
    print(f"Cast-on: {neck_sts} sts")
    print(f"Split:")
    print(f"  Back: {split['back']}")
    print(f"  Front: {split['front']}")
    print(f"  Sleeve L: {split['sleeve_L']}")
    print(f"  Sleeve R: {split['sleeve_R']}")
    print(f"  Plus raglan: 8 sts")

    # With no short rows, front and back should follow the 3:3 ratio
    total_sections = split['back'] + split['front'] + split['sleeve_L'] + split['sleeve_R']
    print(f"  Total sections: {total_sections} (+ 8 raglan = {total_sections + 8})")
    print(f"\nFront:Back ratio: {split['front']}:{split['back']} (should be equal for 3:3 ratio)")

    # In the standard 3:3:2:2 ratio, front should equal back
    assert split['front'] == split['back'], "Front should equal back with no short rows"
    print("\n✓ Test passed!")


if __name__ == "__main__":
    test_xs_with_short_rows()
    test_no_short_rows()
