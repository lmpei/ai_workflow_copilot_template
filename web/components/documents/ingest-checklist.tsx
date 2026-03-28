export default function IngestChecklist() {
  return (
    <ol>
      <li>把文件元数据上传到 API</li>
      <li>把解析和切块任务放入处理队列</li>
      <li>生成向量嵌入</li>
      <li>把向量写入 Chroma</li>
      <li>把文档标记为已索引</li>
    </ol>
  );
}
