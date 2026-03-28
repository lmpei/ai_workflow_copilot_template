"use client";

import SectionCard from "../ui/section-card";

type PublicDemoWorkbenchContinuityNoteProps = {
  moduleType?: "support" | "job" | null;
};

type ContinuityCopy = {
  title: string;
  description: string;
  startPoints: string[];
  boundaries: string[];
};

function getContinuityCopy(moduleType?: "support" | "job" | null): ContinuityCopy {
  if (moduleType === "support") {
    return {
      title: "Support 演示怎么开始",
      description:
        "Support case 现在会持续保存在当前工作区里。这里的重点不是自动清空历史，而是告诉你什么时候该从新工作区开始，什么时候该直接从 case 继续。",
      startPoints: [
        "如果你是在给新观众演示一条干净路径，优先新建引导演示工作区，再按“文档 -> 对话 -> 任务”走一遍。",
        "如果这个工作区里已经有 Support case，要继续同一件事，就直接在 Support case 工作台里点“继续这个 case”。",
        "如果你只是想解释系统已经积累了哪些处理历史，直接打开 case 时间线，不用回任务列表重新拼上下文。",
      ],
      boundaries: [
        "当前页面不会偷偷清空旧 case。",
        "真正的重置属于 operator 操作，不属于页面里的自动行为。",
      ],
    };
  }

  if (moduleType === "job") {
    return {
      title: "Job 演示怎么开始",
      description:
        "Job hiring packet 现在会持续保存在当前工作区里。这里的重点不是自动清空历史，而是告诉你什么时候该从新工作区开始，什么时候该直接从 packet 继续。",
      startPoints: [
        "如果你是在给新观众演示一条干净路径，优先新建引导演示工作区，再按“文档 -> 对话 -> 任务”走一遍。",
        "如果这个工作区里已经有 Job hiring packet，要继续同一个招聘包，就直接在 Job hiring 工作台里点“继续这个 packet”。",
        "如果你只是想解释候选池、短名单和比较历史，直接打开 packet 详情，不用回任务列表重新整理历史。",
      ],
      boundaries: [
        "当前页面不会偷偷清空旧 packet。",
        "真正的重置属于 operator 操作，不属于页面里的自动行为。",
      ],
    };
  }

  return {
    title: "Public Demo 连续性说明",
    description:
      "Stage E 之后，工作区里会持续积累 Support case 和 Job hiring packet。这个 demo 的重点是把起点讲清楚，而不是假装页面每次都会自动回到空白状态。",
    startPoints: [
      "第一次演示时，优先新建引导演示工作区，然后按“文档 -> 对话 -> 任务”走一遍完整路径。",
      "如果你打开的是一个已经有历史的工作区，Support 直接从 case 工作台继续，Job 直接从 hiring packet 工作台继续。",
      "需要一条干净故事线时，正确做法是换一个新的引导演示工作区，而不是复用旧工作区后假装历史不存在。",
    ],
    boundaries: [
      "工作区里的历史允许继续积累。",
      "真正的重置属于 operator 操作，不属于页面里的自动行为。",
    ],
  };
}

export default function PublicDemoWorkbenchContinuityNote({
  moduleType,
}: PublicDemoWorkbenchContinuityNoteProps) {
  const copy = getContinuityCopy(moduleType);

  return (
    <SectionCard title={copy.title} description={copy.description}>
      <div style={{ display: "grid", gap: 12 }}>
        <div>
          <strong>推荐起点</strong>
          <ul style={{ margin: "8px 0 0", paddingLeft: 20 }}>
            {copy.startPoints.map((point) => (
              <li key={point}>{point}</li>
            ))}
          </ul>
        </div>
        <div>
          <strong>边界说明</strong>
          <ul style={{ margin: "8px 0 0", paddingLeft: 20 }}>
            {copy.boundaries.map((point) => (
              <li key={point}>{point}</li>
            ))}
          </ul>
        </div>
      </div>
    </SectionCard>
  );
}
