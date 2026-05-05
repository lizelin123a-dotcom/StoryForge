export type RouteName = 'bookcase' | 'edit' | 'dissect' | 'config' | 'about'
export type StepState = '待执行' | '执行中' | '已完成' | '失败'
export type Chapter = { title: string; content: string; nodeLabel: string; nodesDone: number; nodesTotal: number }
export type RightTab = '监控' | '审阅' | '生成逻辑' | '事件'
