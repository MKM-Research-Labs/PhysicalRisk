# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Console pretty-printer for GBM classifier training results."""


def _print_classifier_result(result: dict) -> None:
    """Print GBM classifier training result."""
    W = 62
    status = result.get("status", "unknown")
    gid = result.get("gauge_id", "")
    print(f"\n{'=' * W}")
    print(f"  Multi-Storm Classifier — {gid}")
    print(f"{'=' * W}")

    if status != "trained":
        print(f"  Status: {status}  ({result.get('reason', '')})")
        print(f"  Positive samples: {result.get('n_positive', 0)}")
        print(f"{'=' * W}\n")
        return

    m = result["metrics"]
    fi = result.get("feature_importance", {})
    label = result.get("label_threshold", "severe_warning")
    label_m = result.get("label_level_m", result.get("severe_level", 0))
    print(f"  Status      : trained")
    print(f"  Label       : {label} (≥ {label_m:.2f} m)")
    print(f"  Samples     : {result['n_samples']:,}  "
          f"(train: {result['n_samples']-result['test_size']:,}  "
          f"test: {result['test_size']:,})")
    print(f"  Flood rate  : {result['flood_rate']:.1%}")
    print()
    print(f"  AUC-ROC     : {m['auc_roc']:.4f}")
    print(f"  Accuracy    : {m['accuracy']:.4f}")
    print(f"  Brier score : {m['brier_score']:.4f}")
    print(f"  Log loss    : {m['log_loss']:.4f}")
    print()
    print(f"  Feature importance:")
    for fname, fval in sorted(fi.items(), key=lambda x: -x[1]):
        bar = "█" * int(fval * 40)
        print(f"    {fname:<18} {fval:.4f}  {bar}")
    print(f"\n  Model saved → {result['model_path']}")
    print(f"{'=' * W}\n")
