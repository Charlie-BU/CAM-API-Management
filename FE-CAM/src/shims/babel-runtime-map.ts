/**
 * 用于兼容 @storage-fe/formily-arco 的生产构建。
 *
 * 该依赖通过 @babel/runtime-corejs3 引入 Map。在 Vite 的生产构建中，
 * 其 CommonJS 包装模块的默认导出可能不再是可调用的构造函数。
 * 应用本身需要 Map，因此直接使用浏览器原生的 Map 构造函数。
 */
export default Map;
