import axios, { AxiosInstance, AxiosRequestConfig } from "axios";
import { RequestInterceptor } from "./requestInterceptor";
import { ResponseInterceptor } from "./responseInterceptor";

/**
 * 基于 axios 的 HTTP 客户端封装
 * 提供统一的 HTTP 请求接口和拦截器机制
 */
export class AxiosClient {
  private instance: AxiosInstance;
  private requestInterceptor: RequestInterceptor;
  private responseInterceptor: ResponseInterceptor;

  constructor(baseURL: string) {
    this.instance = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        "Content-Type": "application/json",
      },
    });

    this.requestInterceptor = new RequestInterceptor();
    this.responseInterceptor = new ResponseInterceptor();

    this.setupInterceptors();
  }

  /**
   * 设置请求和响应拦截器
   */
  private setupInterceptors(): void {
    // 请求拦截器
    this.instance.interceptors.request.use(
      this.requestInterceptor.onRequest.bind(this.requestInterceptor),
      this.requestInterceptor.onRequestError.bind(this.requestInterceptor)
    );

    // 响应拦截器
    this.instance.interceptors.response.use(
      this.responseInterceptor.onResponse.bind(this.responseInterceptor),
      this.responseInterceptor.onResponseError.bind(this.responseInterceptor)
    );
  }

  /**
   * GET 请求
   */
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.get<T>(url, config);
    return response.data;
  }

  /**
   * POST 请求
   */
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.post<T>(url, data, config);
    return response.data;
  }

  /**
   * PUT 请求
   */
  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.put<T>(url, data, config);
    return response.data;
  }

  /**
   * DELETE 请求
   */
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.delete<T>(url, config);
    return response.data;
  }

  /**
   * PATCH 请求
   */
  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.patch<T>(url, data, config);
    return response.data;
  }

  /**
   * 获取 axios 实例（用于高级用法）
   */
  getInstance(): AxiosInstance {
    return this.instance;
  }

  /**
   * 更新基础 URL
   */
  setBaseURL(baseURL: string): void {
    this.instance.defaults.baseURL = baseURL;
  }

  /**
   * 设置认证 token
   */
  setAuthToken(token: string): void {
    this.instance.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  }

  /**
   * 清除认证 token
   */
  clearAuthToken(): void {
    delete this.instance.defaults.headers.common["Authorization"];
  }
}

// 创建默认实例
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
export const axiosClient = new AxiosClient(API_BASE_URL);
