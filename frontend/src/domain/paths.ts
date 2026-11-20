import type { CourseRef } from '../api/types'

/** The course player opened on a topic. */
export const playerPath = (roadmapId: number, item: { course: CourseRef; topic: { id: number } }) =>
  `/roadmaps/${roadmapId}/courses/${item.course.id}?topic=${item.topic.id}`
