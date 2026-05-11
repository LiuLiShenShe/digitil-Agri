<!--
 *   三维数字孪生设计平台
 *
 *  @brief 基于Vue3、Element-Plus、Three.js 构建的 "三维数字孪生项目"
 *
 *    程序主界面入口，全局App组件
 *
 *  @author Sparcle
 *  @version 2.1
 *  @date 2022-7-5
 *  @copyright 2014-2022, Beijing Yupont Electric Power Tech Co., Ltd.
 -->

<template>
  <router-view />
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
  overflow: hidden;
}

body {
  background: #070b18;
}

#app {
  font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  width: 100%;
  height: 100%;
  color: #c8d0da;
}

/* ========== Element Plus 全局覆盖 ========== */

/* 对话框 - 暗色 */
.el-dialog {
  --el-dialog-bg-color: #101826;
  --el-dialog-title-font-size: 16px;
  border-radius: 12px !important;
  border: 1px solid rgba(255,255,255,0.06);
}

.el-dialog__header {
  padding: 20px 24px 0 24px;
}

.el-dialog__body {
  padding: 20px 24px;
}

.el-dialog__footer {
  padding: 0 24px 20px 24px;
}

/* 树控件 */
.el-tree {
  background: transparent !important;
  color: #bcc8d4;
}

.el-tree-node__content:hover {
  background: rgba(255,255,255,0.04) !important;
}

.el-tree-node.is-current > .el-tree-node__content {
  background: rgba(0,212,255,0.1) !important;
  color: #00d4ff !important;
}

/* 菜单 */
.head-sub-menu {
  --el-menu-bg-color: rgba(16,24,38,0.95);
  --el-fill-color-blank: transparent;
  background: rgba(16,24,38,0.95) !important;
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.08) !important;
  border-radius: 8px !important;
  overflow: hidden;
}

.head-sub-menu .el-menu {
  --el-menu-bg-color: transparent;
  --el-fill-color-blank: transparent;
  background-color: transparent;
  border: none !important;
}

.head-sub-menu .el-menu-item {
  color: #bcc8d4 !important;
}

.head-sub-menu .el-menu-item:hover {
  background: rgba(0,212,255,0.1) !important;
  color: #00d4ff !important;
}

/* 折叠面板 */
.el-collapse {
  --el-collapse-header-bg-color: transparent;
  --el-collapse-content-bg-color: transparent;
  border: none;
}

/* 输入框 */
.el-input__wrapper {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(255,255,255,0.08);
}

.el-input__inner {
  color: #c8d0da !important;
}

/* 滑块 */
.el-slider__runway {
  background: rgba(255,255,255,0.08) !important;
}

.el-slider__bar {
  background: linear-gradient(90deg, #4090ff, #00d4ff) !important;
}

.el-slider__button {
  border-color: #00d4ff !important;
}

/* 选择器 */
.el-select .el-input__wrapper {
  background: rgba(255,255,255,0.04) !important;
}

/* 单选框按钮 */
.el-radio-button__inner {
  background: rgba(255,255,255,0.04) !important;
  border-color: rgba(255,255,255,0.08) !important;
  color: #8899aa !important;
}

.el-radio-button.is-active .el-radio-button__inner {
  background: rgba(0,212,255,0.15) !important;
  border-color: rgba(0,212,255,0.3) !important;
  color: #00d4ff !important;
  box-shadow: none !important;
}

/* 开关 */
.el-switch.is-checked .el-switch__core {
  background: #00d4ff !important;
  border-color: #00d4ff !important;
}

/* 分页 */
.el-tabs__item {
  color: #8899aa !important;
}

.el-tabs__item.is-active {
  color: #00d4ff !important;
}

.el-tabs__active-bar {
  background: #00d4ff !important;
}

/* 上传拖拽 */
.el-upload-dragger {
  background: rgba(255,255,255,0.03) !important;
  border: 1px dashed rgba(255,255,255,0.12) !important;
  border-radius: 8px !important;
}

.el-upload-dragger:hover {
  border-color: #4090ff !important;
}

/* 分割线 */
.el-divider--horizontal {
  border-color: rgba(255,255,255,0.06) !important;
}

/* 描述列表 */
.el-descriptions__label {
  font-size: 12px !important;
}

.el-descriptions__content {
  font-size: 13px !important;
}

/* 进度条 */
.el-progress-bar__outer {
  background: rgba(255,255,255,0.08) !important;
}

/* 滚动条 */
::-webkit-scrollbar {
  width: 5px;
  height: 5px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.12);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(255,255,255,0.2);
}
</style>
