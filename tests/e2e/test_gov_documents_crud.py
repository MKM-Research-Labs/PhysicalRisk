# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Governance e2e test: document upload/download tab.
Split from test_governance_crud.py.
"""

import pytest

from tests.e2e.helpers import (
    close_all_panels,
    get_governance_content_text,
    open_governance,
    switch_governance_tab,
)


class TestDocumentUploadDownload:
    """Documents tab — upload area, document list, download buttons."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        close_all_panels(map_page)
        open_governance(map_page)
        switch_governance_tab(map_page, "documents")
        yield
        close_all_panels(map_page)

    def test_upload_area_exists(self, map_page):
        """Documents tab should have an upload area or upload button."""
        content = map_page.locator("#mg-content")
        assert content.count() > 0, "No content area found"

        # Look for file input, drop zone, or upload button
        file_input = content.locator("input[type='file']")
        upload_btn = content.locator("button").filter(has_text="Upload").or_(
            content.locator("button").filter(has_text="upload")
        ).or_(
            content.locator("[class*='upload']")
        ).or_(
            content.locator("[class*='drop']")
        )
        has_upload = file_input.count() > 0 or upload_btn.count() > 0

        if not has_upload:
            # Check for any upload-related text
            text = get_governance_content_text(map_page)
            has_upload = "upload" in text or "drop" in text or "choose" in text

        assert has_upload, "No upload area, file input, or upload button found"

    def test_document_list_renders(self, map_page):
        """Documents tab should render a document list (table or list)."""
        content = map_page.locator("#mg-content")
        assert content.count() > 0

        table = content.locator("table")
        list_el = content.locator("ul, ol, [class*='list'], [class*='doc']")

        has_list = table.count() > 0 or list_el.count() > 0
        if not has_list:
            # Fallback: check for any document-related content
            text = get_governance_content_text(map_page)
            has_list = "document" in text or "file" in text or ".pdf" in text

        assert has_list, "No document list (table or list element) found"

    def test_download_buttons_clickable(self, map_page):
        """If download buttons exist, they should be clickable."""
        content = map_page.locator("#mg-content")
        download_btns = content.locator("button").filter(has_text="Download").or_(
            content.locator("a[download]")
        ).or_(
            content.locator("button").filter(has_text="download")
        ).or_(
            content.locator("[title*='Download']")
        ).or_(
            content.locator("[title*='download']")
        )

        if download_btns.count() == 0:
            pytest.skip("No download buttons found in documents tab")

        # Verify first download button is enabled and clickable
        first_btn = download_btns.first
        assert first_btn.is_visible(), "Download button is not visible"
        assert first_btn.is_enabled(), "Download button is not enabled"
