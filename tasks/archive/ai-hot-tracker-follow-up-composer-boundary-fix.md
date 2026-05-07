# AI 热点追踪追问输入区边界修复

## Objective

修复 `AI 热点追踪` 右侧追问输入区和发送按钮在面板底部、右侧边界被裁切的问题。

## Scope

- 给右侧追问面板底部增加安全空间，避免输入区贴住容器边缘。
- 将追问输入区改成更紧凑的一行式 composer。
- 限制发送按钮宽度，避免按钮被输入框挤出面板。
- 明确输入框 `min-width: 0`，防止 CSS grid 中 textarea 横向溢出。

## Verification

- `npm --prefix web run verify`
- 公网页面手工检查右侧追问输入框和发送按钮完整可见。
