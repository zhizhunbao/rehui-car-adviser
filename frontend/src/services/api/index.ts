// API 服务导出
export { ApiService, apiService } from "./api";

// 导入 apiService 实例用于创建绑定函数
import { apiService } from "./api";

// 直接导出常用的 API 方法，方便使用
export const sendConversationMessage = apiService.sendConversationMessage.bind(apiService);
export const searchCars = apiService.searchCars.bind(apiService);
export const getCarDetails = apiService.getCarDetails.bind(apiService);
export const getCarsList = apiService.getCarsList.bind(apiService);
export const login = apiService.login.bind(apiService);
export const register = apiService.register.bind(apiService);
export const logout = apiService.logout.bind(apiService);
export const getUserProfile = apiService.getUserProfile.bind(apiService);
export const updateUserProfile = apiService.updateUserProfile.bind(apiService);