import { axiosClient } from "../http";
import { logger } from "../../utils/logger";
import { 
  SearchRequest, 
  SearchResponse, 
  SendMessageRequest, 
  SendMessageResponse,
  CarDetails,
  CarListItem,
  LoginCredentials,
  RegisterData,
  UserProfile
} from "../../types";

/**
 * 统一的 API 服务类
 * 提供所有后端 API 的调用接口
 */
export class ApiService {
  /**
   * 搜索汽车
   */
  async searchCars(query: string): Promise<SearchResponse> {
    logger.logResult("API调用", `POST /api/search, 查询: ${query}`);
    
    try {
      const response = await axiosClient.post<SearchResponse>("/api/search", {
        query,
      } as SearchRequest);
      
      logger.logResult("搜索成功", `返回${response.total}条结果`);
      
      return response;
    } catch (error: any) {
      logger.logResult("搜索错误", error.toString());
      return {
        results: [],
        total: 0,
        page: 1,
        limit: 20,
        hasMore: false,
      };
    }
  }

  /**
   * 发送对话消息
   */
  async sendConversationMessage(request: SendMessageRequest): Promise<SendMessageResponse> {
    logger.logResult("API调用", `POST /api/conversation, 消息: ${request.message.substring(0, 50)}...`);
    
    try {
      const response = await axiosClient.post<SendMessageResponse>("/api/conversation", request);
      
      // 后端返回的message是字符串，需要转换为Message对象
      const messageObj = {
        id: Date.now().toString(),
        role: 'assistant' as const,
        content: response.message,
        timestamp: Date.now(),
        metadata: {
          model: 'gemini-2.5-flash'
        }
      };
      
      logger.logResult("对话成功", `AI回复长度: ${messageObj.content.length}`);
      
      return {
        ...response,
        message: messageObj
      };
    } catch (error: any) {
      logger.logResult("对话错误", error.toString());
      throw new Error(error.message || "对话失败，请稍后重试");
    }
  }

  /**
   * 获取汽车详情
   */
  async getCarDetails(carId: string): Promise<CarDetails | null> {
    logger.logResult("API调用", `GET /api/cars/${carId}`);
    
    try {
      const response = await axiosClient.get<CarDetails>(`/api/cars/${carId}`);
      logger.logResult("获取汽车详情成功", `ID: ${carId}`);
      return response;
    } catch (error: any) {
      logger.logResult("获取汽车详情失败", error.toString());
      return null;
    }
  }

  /**
   * 获取汽车列表
   */
  async getCarsList(page: number = 1, limit: number = 20): Promise<{ cars: CarListItem[]; total: number }> {
    logger.logResult("API调用", `GET /api/cars?page=${page}&limit=${limit}`);
    
    try {
      const response = await axiosClient.get<{ cars: CarListItem[]; total: number }>(`/api/cars?page=${page}&limit=${limit}`);
      logger.logResult("获取汽车列表成功", `第${page}页，共${response.total}条`);
      return response;
    } catch (error: any) {
      logger.logResult("获取汽车列表失败", error.toString());
      return { cars: [], total: 0 };
    }
  }

  /**
   * 用户登录
   */
  async login(credentials: LoginCredentials): Promise<{ success: boolean; token?: string; user?: UserProfile; error?: string }> {
    logger.logResult("API调用", `POST /auth/login`);
    
    try {
      const response = await axiosClient.post<{ success: boolean; token?: string; user?: UserProfile; error?: string }>("/auth/login", credentials);
      
      if (response.success && response.token) {
        // 设置认证 token
        axiosClient.setAuthToken(response.token);
        logger.logResult("登录成功", `用户: ${response.user?.username}`);
      } else {
        logger.logResult("登录失败", response.error || "未知错误");
      }
      
      return response;
    } catch (error: any) {
      logger.logResult("登录错误", error.toString());
      return {
        success: false,
        error: error.message || "登录失败，请检查用户名和密码",
      };
    }
  }

  /**
   * 用户注册
   */
  async register(userData: RegisterData): Promise<{ success: boolean; message?: string; error?: string }> {
    logger.logResult("API调用", `POST /auth/register`);
    
    try {
      const response = await axiosClient.post<{ success: boolean; message?: string; error?: string }>("/auth/register", userData);
      
      if (response.success) {
        logger.logResult("注册成功", response.message || "用户注册成功");
      } else {
        logger.logResult("注册失败", response.error || "未知错误");
      }
      
      return response;
    } catch (error: any) {
      logger.logResult("注册错误", error.toString());
      return {
        success: false,
        error: error.message || "注册失败，请稍后重试",
      };
    }
  }

  /**
   * 用户登出
   */
  async logout(): Promise<void> {
    logger.logResult("API调用", `POST /auth/logout`);
    
    try {
      await axiosClient.post("/auth/logout");
      axiosClient.clearAuthToken();
      logger.logResult("登出成功", "用户已登出");
    } catch (error: any) {
      logger.logResult("登出错误", error.toString());
      // 即使登出失败，也清除本地 token
      axiosClient.clearAuthToken();
    }
  }

  /**
   * 获取用户信息
   */
  async getUserProfile(): Promise<UserProfile | null> {
    logger.logResult("API调用", `GET /auth/profile`);
    
    try {
      const response = await axiosClient.get<UserProfile>("/auth/profile");
      logger.logResult("获取用户信息成功", `用户: ${response.username}`);
      return response;
    } catch (error: any) {
      logger.logResult("获取用户信息失败", error.toString());
      return null;
    }
  }

  /**
   * 更新用户信息
   */
  async updateUserProfile(userData: Partial<UserProfile>): Promise<{ success: boolean; user?: UserProfile; error?: string }> {
    logger.logResult("API调用", `PUT /auth/profile`);
    
    try {
      const response = await axiosClient.put<{ success: boolean; user?: UserProfile; error?: string }>("/auth/profile", userData);
      
      if (response.success) {
        logger.logResult("更新用户信息成功", `用户: ${response.user?.username}`);
      } else {
        logger.logResult("更新用户信息失败", response.error || "未知错误");
      }
      
      return response;
    } catch (error: any) {
      logger.logResult("更新用户信息错误", error.toString());
      return {
        success: false,
        error: error.message || "更新失败，请稍后重试",
      };
    }
  }
}

// 创建默认实例
export const apiService = new ApiService();