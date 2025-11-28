<template>
  <div class="user-float-button" v-if="!isAnonymous">
    <Popover 
      trigger="click" 
      v-model:visible="showPopover"
      placement="top-end"
    >
      <template #content>
        <div class="user-popover">
          <div class="user-header">
            <div class="avatar">
              <IconUser size="24" />
            </div>
            <div class="info">
              <div class="username">{{ authStore.username }}</div>
              <div class="role">
                <span :class="['role-tag', authStore.isAdmin ? 'admin' : 'user']">
                  {{ authStore.isAdmin ? '管理员' : '普通用户' }}
                </span>
              </div>
            </div>
          </div>
          
          <div class="divider"></div>
          
          <div class="menu-list">
            <div class="menu-item" @click="handleChangePassword">
              <IconLock />
              <span>修改密码</span>
            </div>
            <div class="menu-item logout" @click="handleLogout">
              <IconLogout />
              <span>退出登录</span>
            </div>
          </div>
        </div>
      </template>
      
      <div class="float-btn">
        <IconUser size="20" />
      </div>
    </Popover>
    
    <!-- 修改密码对话框 -->
    <Modal
      v-model:visible="showPasswordModal"
      title="修改密码"
      :width="400"
      @confirm="submitPasswordChange"
      :confirmLoading="passwordLoading"
    >
      <div class="password-form">
        <div class="form-item">
          <label>当前密码</label>
          <Input 
            v-model:value="passwordForm.oldPassword" 
            type="password" 
            placeholder="请输入当前密码"
          />
        </div>
        <div class="form-item">
          <label>新密码</label>
          <Input 
            v-model:value="passwordForm.newPassword" 
            type="password" 
            placeholder="请输入新密码"
          />
        </div>
        <div class="form-item">
          <label>确认新密码</label>
          <Input 
            v-model:value="passwordForm.confirmPassword" 
            type="password" 
            placeholder="请再次输入新密码"
          />
        </div>
        <div v-if="passwordError" class="error-msg">{{ passwordError }}</div>
      </div>
    </Modal>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useAuthStore } from '@/store/auth'
import { 
  User as IconUser, 
  Lock as IconLock,
  Logout as IconLogout,
} from '@icon-park/vue-next'
import Popover from '@/components/Popover.vue'
import Modal from '@/components/Modal.vue'
import Input from '@/components/Input.vue'
import message from '@/utils/message'

const authStore = useAuthStore()
const { isLoggedIn } = storeToRefs(authStore)

// 是否是匿名用户
const isAnonymous = computed(() => !isLoggedIn.value)

// Popover 显示状态
const showPopover = ref(false)

// 修改密码相关
const showPasswordModal = ref(false)
const passwordLoading = ref(false)
const passwordError = ref('')
const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
})

// 处理修改密码
function handleChangePassword() {
  showPopover.value = false
  passwordForm.value = {
    oldPassword: '',
    newPassword: '',
    confirmPassword: '',
  }
  passwordError.value = ''
  showPasswordModal.value = true
}

// 提交密码修改
async function submitPasswordChange() {
  const { oldPassword, newPassword, confirmPassword } = passwordForm.value
  
  // 验证
  if (!oldPassword || !newPassword || !confirmPassword) {
    passwordError.value = '请填写所有字段'
    return
  }
  
  if (newPassword.length < 6) {
    passwordError.value = '新密码至少6个字符'
    return
  }
  
  if (newPassword !== confirmPassword) {
    passwordError.value = '两次输入的新密码不一致'
    return
  }
  
  passwordLoading.value = true
  passwordError.value = ''
  
  try {
    const result = await authStore.changePassword(oldPassword, newPassword)
    if (result.success) {
      message.success('密码修改成功')
      showPasswordModal.value = false
    }
    else {
      passwordError.value = result.message
    }
  }
  finally {
    passwordLoading.value = false
  }
}

// 处理登出
async function handleLogout() {
  showPopover.value = false
  await authStore.logout()
  // 清除匿名访问标记，强制显示登录页
  localStorage.removeItem('skip_login')
  // 刷新页面
  window.location.reload()
}
</script>

<style lang="scss" scoped>
.user-float-button {
  position: fixed;
  bottom: 80px;
  right: 20px;
  z-index: 1000;
}

.float-btn {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  transition: all 0.2s;
  
  &:hover {
    transform: scale(1.1);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
  }
}

.user-popover {
  width: 220px;
  padding: 12px 0;
}

.user-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 16px 12px;
  
  .avatar {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .info {
    flex: 1;
    min-width: 0;
  }
  
  .username {
    font-size: 15px;
    font-weight: 600;
    color: #333;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .role-tag {
    display: inline-block;
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 10px;
    margin-top: 4px;
    
    &.admin {
      background: #fff1f0;
      color: #ff4d4f;
    }
    
    &.user {
      background: #f0f5ff;
      color: #1890ff;
    }
  }
}

.divider {
  height: 1px;
  background: #f0f0f0;
  margin: 8px 0;
}

.menu-list {
  .menu-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 16px;
    cursor: pointer;
    transition: background 0.2s;
    color: #666;
    font-size: 14px;
    
    &:hover {
      background: #f5f5f5;
      color: #333;
    }
    
    &.logout {
      color: #ff4d4f;
      
      &:hover {
        background: #fff1f0;
        color: #ff4d4f;
      }
    }
  }
}

.password-form {
  .form-item {
    margin-bottom: 16px;
    
    label {
      display: block;
      font-size: 13px;
      color: #666;
      margin-bottom: 6px;
    }
  }
  
  .error-msg {
    color: #ff4d4f;
    font-size: 13px;
    margin-top: -8px;
  }
}
</style>
