export default function IngestChecklist() {
  return (
    <ol>
      <li>Upload file metadata to the API</li>
      <li>Queue parsing and chunking work</li>
      <li>Generate embeddings</li>
      <li>Write vectors to Chroma</li>
      <li>Mark the document as indexed</li>
    </ol>
  );
}
