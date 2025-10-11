// 验证工具函数

// 邮箱验证
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

// 手机号验证
export const isValidPhone = (phone: string): boolean => {
  const phoneRegex = /^1[3-9]\d{9}$/;
  return phoneRegex.test(phone);
};

// URL验证
export const isValidUrl = (url: string): boolean => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

// 身份证号验证
export const isValidIdCard = (idCard: string): boolean => {
  const idCardRegex = /(^\d{15}$)|(^\d{18}$)|(^\d{17}(\d|X|x)$)/;
  return idCardRegex.test(idCard);
};

// 密码强度验证
export const validatePassword = (password: string): {
  isValid: boolean;
  strength: 'weak' | 'medium' | 'strong';
  errors: string[];
} => {
  const errors: string[] = [];
  let strength: 'weak' | 'medium' | 'strong' = 'weak';

  if (password.length < 8) {
    errors.push('密码长度至少8位');
  }

  if (!/[A-Z]/.test(password)) {
    errors.push('密码必须包含大写字母');
  }

  if (!/[a-z]/.test(password)) {
    errors.push('密码必须包含小写字母');
  }

  if (!/\d/.test(password)) {
    errors.push('密码必须包含数字');
  }

  if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    errors.push('密码必须包含特殊字符');
  }

  // 计算密码强度
  if (errors.length === 0) {
    strength = 'strong';
  } else if (errors.length <= 2) {
    strength = 'medium';
  }

  return {
    isValid: errors.length === 0,
    strength,
    errors,
  };
};

// 表单验证规则
export interface ValidationRule {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: RegExp;
  custom?: (value: any) => boolean | string;
  message?: string;
}

// 表单验证器
export class FormValidator {
  private rules: Record<string, ValidationRule[]> = {};

  // 添加验证规则
  addRule(field: string, rule: ValidationRule) {
    if (!this.rules[field]) {
      this.rules[field] = [];
    }
    this.rules[field].push(rule);
  }

  // 验证单个字段
  validateField(field: string, value: any): string | null {
    const fieldRules = this.rules[field] || [];
    
    for (const rule of fieldRules) {
      const error = this.validateRule(value, rule);
      if (error) {
        return error;
      }
    }
    
    return null;
  }

  // 验证整个表单
  validateForm(data: Record<string, any>): Record<string, string> {
    const errors: Record<string, string> = {};
    
    Object.keys(this.rules).forEach(field => {
      const error = this.validateField(field, data[field]);
      if (error) {
        errors[field] = error;
      }
    });
    
    return errors;
  }

  // 验证单个规则
  private validateRule(value: any, rule: ValidationRule): string | null {
    // 必填验证
    if (rule.required && (value === null || value === undefined || value === '')) {
      return rule.message || '此字段为必填项';
    }

    // 如果值为空且不是必填，跳过其他验证
    if (!rule.required && (value === null || value === undefined || value === '')) {
      return null;
    }

    // 最小长度验证
    if (rule.minLength && typeof value === 'string' && value.length < rule.minLength) {
      return rule.message || `长度不能少于${rule.minLength}个字符`;
    }

    // 最大长度验证
    if (rule.maxLength && typeof value === 'string' && value.length > rule.maxLength) {
      return rule.message || `长度不能超过${rule.maxLength}个字符`;
    }

    // 正则表达式验证
    if (rule.pattern && typeof value === 'string' && !rule.pattern.test(value)) {
      return rule.message || '格式不正确';
    }

    // 自定义验证
    if (rule.custom) {
      const result = rule.custom(value);
      if (result !== true) {
        return typeof result === 'string' ? result : (rule.message || '验证失败');
      }
    }

    return null;
  }

  // 清除规则
  clearRules(field?: string) {
    if (field) {
      delete this.rules[field];
    } else {
      this.rules = {};
    }
  }
}

// 常用验证规则
export const commonValidationRules = {
  email: {
    required: true,
    pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    message: '请输入有效的邮箱地址',
  },
  phone: {
    required: true,
    pattern: /^1[3-9]\d{9}$/,
    message: '请输入有效的手机号码',
  },
  password: {
    required: true,
    minLength: 8,
    pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}$/,
    message: '密码必须包含大小写字母、数字和特殊字符，长度至少8位',
  },
  username: {
    required: true,
    minLength: 3,
    maxLength: 20,
    pattern: /^[a-zA-Z0-9_]+$/,
    message: '用户名只能包含字母、数字和下划线，长度3-20位',
  },
  url: {
    pattern: /^https?:\/\/.+/,
    message: '请输入有效的URL地址',
  },
  number: {
    pattern: /^\d+$/,
    message: '请输入有效的数字',
  },
  positiveNumber: {
    custom: (value: any) => {
      const num = Number(value);
      return !isNaN(num) && num > 0;
    },
    message: '请输入大于0的数字',
  },
};

// 创建验证器实例
export const createValidator = () => new FormValidator();
