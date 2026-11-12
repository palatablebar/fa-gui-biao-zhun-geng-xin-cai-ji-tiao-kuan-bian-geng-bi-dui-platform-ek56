export const ERROR_MESSAGES: Record<string, string> = {
  AUTH_REQUIRED: '请先登录',
  AUTH_INVALID: '邮箱或密码不正确',
  TOKEN_EXPIRED: '登录已过期，请重新登录',
  FORBIDDEN: '当前角色无权执行该操作',
  NOT_FOUND: '对象不存在',
  VALIDATION_ERROR: '请求参数不合法',
  SOURCE_DISABLED: '该来源已停用，不能发起采集',
  NO_NEW_VERSION: '该来源暂无待采集的新版本',
  DOCUMENT_EMPTY: '文档正文为空，无法切分条款',
  SAME_VERSION: '左右版本相同，无需比对',
  DIFF_TOO_LARGE: '条款数量超出比对上限',
  DIFF_NOT_READY: '比对尚未完成',
  DIFF_FAILED: '比对执行失败',
  CHANGE_NOT_CONFIRMED: '先确认至少一条变更才能发布',
  ALREADY_CONFIRMED: '该变更已确认',
  ALREADY_PUBLISHED: '该变更已发布',
  RATE_LIMITED: '请求过于频繁，请稍后重试',
  INTERNAL_ERROR: '服务内部错误',
}

export const EMPTY_COPY = {
  sources: '来源还没有接入：先在后端 seed 里登记来源，再回来看采集队列。',
  versions: '这部法规还没有版本：点「采集新版本」把来源里发布的最新版拉进台账。',
  runs: '还没有比对批次：选一个旧版本和新版本，发起第一次条款比对。',
  changes: '这个批次的 9 条变更都以「未确认」状态等着——先确认 2 条并标注影响行业。',
  published: '客户视图为空：确认变更后点「发布」，发布说明才会出现在这里。',
}
