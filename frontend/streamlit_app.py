# -*- coding: utf-8 -*-
"""
Streamlit Web 前端

基于 Streamlit 的 Web UI 实现。
通过 API 客户端与后端通信，实现前后端分离。
"""
from __future__ import annotations

import os
from typing import Any, List

import streamlit as st

from frontend.api_client import APIClient
from frontend.components.sidebar import render_sidebar, SidebarState
from frontend.components.main_view import render_main_view
from frontend.constants import (
    APP_DESCRIPTION,
    APP_TITLE,
    NO_FILES_INFO,
    PAGE_ICON,
    PAGE_LAYOUT,
    PAGE_TITLE,
    UPLOAD_LABEL,
    UPLOAD_TYPES,
)
from core.spectrum import read_spectrum


def run() -> None:
    """运行 Streamlit 应用"""
    st.set_page_config(page_title=PAGE_TITLE, layout=PAGE_LAYOUT, page_icon=PAGE_ICON)
    st.title(APP_TITLE)
    st.markdown(APP_DESCRIPTION)

    uploaded_files: List[Any] | None = st.file_uploader(
        UPLOAD_LABEL,
        type=UPLOAD_TYPES,
        accept_multiple_files=True,
    )

    sidebar_state = render_sidebar(uploaded_files)

    if not uploaded_files:
        st.info(NO_FILES_INFO)
        return

    try:
        spectra = [read_spectrum(f.getvalue(), source_name=f.name) for f in uploaded_files]
        render_main_view(uploaded_files=uploaded_files, spectra=spectra, sidebar=sidebar_state)
    except Exception as exc:
        st.error(f"处理错误: {exc}")


if __name__ == "__main__":
    run()
