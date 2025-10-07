import axios from 'axios';
import { SearchRequest, SearchResponse } from '../types';
import { logger } from '../utils/logger';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

export const searchCars = async (query: string): Promise<SearchResponse> => {
  // 关键部位日志：外部调用 - API请求
  logger.logResult("发送API请求", `POST /api/search, 查询: ${query}`);
  
  try {
    const response = await api.post<SearchResponse>('/api/search', {
      query,
    } as SearchRequest);
    
    if (response.data.success) {
      // 关键部位日志：状态变化 - API响应成功
      logger.logResult("API请求成功", `返回${response.data.total_count}条结果`);
    } else {
      logger.logResult("API请求失败", `错误: ${response.data.error}`);
    }
    
    return response.data;
  } catch (error) {
    // 关键部位日志：错误处理
    if (axios.isAxiosError(error)) {
      const errorMessage = error.response?.data?.error || error.message || '搜索失败，请稍后重试';
      logger.logResult("API请求失败", `错误: ${errorMessage}`);
      return {
        success: false,
        error: errorMessage,
      };
    }
    
    logger.logResult("API请求失败", "网络错误");
    return {
      success: false,
      error: '网络错误，请检查网络连接',
    };
  }
};
