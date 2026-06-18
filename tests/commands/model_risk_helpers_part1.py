# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Shared helpers and factory functions for model_risk report tests (part 1)."""


# ---------------------------------------------------------------------------
# Factory functions
# ---------------------------------------------------------------------------

def _make_model(model_id='M-001', tier=1, rag='Green', stage='Production',
                owner='Alice', peer_reviewer='Bob', next_review='2026-06-01',
                validation_questions=None, remediation_steps=None,
                assumptions=None, limitations=None, test_coverage=None,
                overall_risk_rating=None):
    """Build a sample model dict."""
    m = {
        'model_id': model_id,
        'name': f'Model {model_id}',
        'short_name': f'Mdl {model_id}',
        'tier': tier,
        'rag_rating': rag,
        'lifecycle_stage': stage,
        'owner': owner,
        'peer_reviewer': peer_reviewer,
        'next_review_date': next_review,
        'validation_questions': validation_questions or [],
        'remediation_steps': remediation_steps or [],
        'assumptions': assumptions or [],
        'limitations': limitations or [],
        'test_coverage': test_coverage or {},
    }
    if overall_risk_rating:
        m['overall_risk_rating'] = overall_risk_rating
    return m


def _make_meeting(mid='MRC-001', title='Quarterly Review', date='2026-01-15',
                  status='Completed', decisions=None, actions=None):
    return {
        'id': mid,
        'title': title,
        'date': date,
        'status': status,
        'decisions': decisions or [],
        'actions': actions or [],
    }


def _make_bcbs(principles=None, assessment_date='2026-01-20',
               assessor='Risk Team'):
    return {
        'assessment_date': assessment_date,
        'assessor': assessor,
        'principles': principles or [],
    }


def _make_principle(pid=1, title='Governance', category='Overarching',
                    score=3, max_score=4, status='Largely Compliant',
                    gaps=None):
    p = {
        'id': pid,
        'title': title,
        'category': category,
        'score': score,
        'max_score': max_score,
        'status': status,
    }
    if gaps:
        p['gaps'] = gaps
    return p


def _make_raci(roles=None, activities=None, escalation_triggers=None):
    return {
        'roles': roles or [],
        'activities': activities or [],
        'escalation_triggers': escalation_triggers or [],
    }


def _make_role(label='Model Owner', raci_code='R', assigned_to='Alice',
               backup='Bob'):
    return {
        'label': label,
        'raci_code': raci_code,
        'assigned_to': assigned_to,
        'backup': backup,
    }
