"use client";

import SectionCard from "../ui/section-card";

type PublicDemoWorkbenchContinuityNoteProps = {
  moduleType?: "support" | "job" | null;
};

function buildContinuityPoints(moduleType?: "support" | "job" | null): string[] {
  if (moduleType === "support") {
    return [
      "当前工作区里的 Support 任务会继续写入已有 Support case 和 case 时间线，不会在页面里被悄悄清空。",
      "如果你要给新观众展示一条干净的 Support 路径，优先新建一个引导演示工作区，而不是手工复用旧 case。",
      "真正的重置属于运维动作，不属于页面内自动清理。",
    ];
  }

  if (moduleType === "job") {
    return [
      "当前工作区里的 Job 任务会继续写入已有 hiring packet、候选池和 shortlist 历史，不会在页面里被悄悄清空。",
      "如果你要给新观众展示一条干净的 Job 路径，优先新建一个引导演示工作区，而不是手工复用旧 packet。",
      "真正的重置属于运维动作，不属于页面内自动清理。",
    ];
  }

  return [
    "这个 public demo 会保留当前工作区中的文档、任务历史，以及后续生成的 Support case / Job hiring packet 等持久对象。",
    "如果你要给新观众展示一条干净路径，优先新建一个引导演示工作区，而不是假设系统会自动清空旧状态。",
    "真正的重置属于运维动作，不属于页面内自动清理。",
  ];
}

export default function PublicDemoWorkbenchContinuityNote({
  moduleType,
}: PublicDemoWorkbenchContinuityNoteProps) {
  return (
    <SectionCard
      title="演示连续性说明"
      description="Stage E 引入了持久 workbench 对象。它们会在当前工作区里继续积累，但这个公网 demo 仍然保持 demo-grade 和有边界的重置方式。"
    >
      <ul style={{ margin: 0, paddingLeft: 20 }}>
        {buildContinuityPoints(moduleType).map((point) => (
          <li key={point}>{point}</li>
        ))}
      </ul>
    </SectionCard>
  );
}
