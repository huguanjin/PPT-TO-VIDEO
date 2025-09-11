/**
 * 增强版视频导出功能
 * 支持保存到output目录，模拟服务器端文件保存
 */
import { ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useSlidesStore } from '@/store'
import { toPng } from 'html-to-image'

export default function useEnhancedVideoExport() {
  const exporting = ref(false)
  const slidesStore = useSlidesStore()
  const { slides, title, theme, viewportSize, viewportRatio } = storeToRefs(slidesStore)

  /**
   * 导出到指定目录（如果在Electron环境中）
   */
  const exportToOutputDirectory = async () => {
    try {
      exporting.value = true

      // 检查是否在Electron环境中
      if (typeof window !== 'undefined' && (window as any).electronAPI) {
        // Electron环境：使用IPC与主进程通信
        await exportViaElectron()
      }
      else {
        // 浏览器环境：使用下载功能
        await exportViaDownload()
      }
    }
    catch (error) {
      // eslint-disable-next-line no-console
      console.error('导出失败:', error)
      throw error
    }
    finally {
      exporting.value = false
    }
  }

  /**
   * 通过Electron导出（如果可用）
   */
  const exportViaElectron = async () => {
    // 这里需要与Electron主进程通信
    // 暂时使用下载方式替代
    return await exportViaDownload()
  }

  /**
   * 通过浏览器下载方式导出
   */
  const exportViaDownload = async () => {
    // 1. 生成项目文件夹名称
    const projectName = (title.value || 'pptist_project').replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '_')
    const timestamp = new Date().toISOString().slice(0, 19).replace(/[:]/g, '-')
    const folderName = `${projectName}_${timestamp}`

    // 2. 准备JSON数据
    const exportData = {
      project_name: projectName,
      title: title.value || 'Untitled Presentation',
      width: viewportSize.value,
      height: viewportSize.value * viewportRatio.value,
      theme: theme.value,
      slides: slides.value.map((slide, index) => ({
        slide_id: String(index + 1).padStart(3, '0'),
        slide_number: index + 1,
        title: extractSlideTitle(slide),
        image_file: `slide_${String(index + 1).padStart(3, '0')}.png`,
        notes: slide.remark || '', // 备注信息（讲话稿）
        notes_word_count: (slide.remark || '').length,
        background: slide.background,
        elements: slide.elements,
        extracted_at: new Date().toISOString()
      })),
      total_slides: slides.value.length,
      parsing_completed: true,
      parsing_timestamp: new Date().toISOString(),
      source_file: `${title.value || 'presentation'}.pptist`,
      export_type: 'video_generation_enhanced'
    }

    // 3. 创建并下载说明文件
    downloadReadmeFile(folderName, exportData)

    // 4. 下载JSON文件
    const jsonBlob = new Blob([JSON.stringify(exportData, null, 2)], { 
      type: 'application/json;charset=utf-8' 
    })
    downloadFile(jsonBlob, `${folderName}_slides_metadata.json`)

    // 等待一下再下载图片
    await new Promise(resolve => setTimeout(resolve, 500))

    // 5. 导出幻灯片图片
    await exportSlidesAsImages()

    return { folderName, exportData }
  }

  /**
   * 下载说明文件
   */
  const downloadReadmeFile = (folderName: string, exportData: any) => {
    const readmeContent = generateReadmeContent(folderName, exportData)
    const readmeBlob = new Blob([readmeContent], { 
      type: 'text/plain;charset=utf-8' 
    })
    downloadFile(readmeBlob, `${folderName}_README.txt`)
  }

  /**
   * 生成说明文件内容
   */
  const generateReadmeContent = (folderName: string, exportData: any) => {
    return `PPTist 导出文件说明
===================

项目名称: ${exportData.title}
导出时间: ${new Date().toLocaleString('zh-CN')}
文件夹名: ${folderName}
幻灯片数量: ${exportData.total_slides}

文件列表:
1. ${folderName}_slides_metadata.json - 幻灯片元数据文件
2. slide_001.png ~ slide_${String(exportData.total_slides).padStart(3, '0')}.png - 幻灯片图片文件
3. ${folderName}_README.txt - 本说明文件

使用方法:
1. 将所有文件放入PPT转视频工具的input目录
2. 选择"PPTist导出文件"模式
3. 上传JSON文件和对应的图片文件
4. 开始视频生成流程

技术信息:
- 图片尺寸: ${exportData.width} x ${exportData.height}
- 导出格式: PNG (高质量)
- 元数据格式: JSON
- 编码: UTF-8

注意事项:
- 请保持文件名不变，以确保正确关联
- 建议将所有文件放在同一目录下
- 备注信息已包含在JSON文件的remark字段中
`
  }

  /**
   * 导出所有幻灯片为图片
   */
  const exportSlidesAsImages = async () => {
    // 查找幻灯片画布元素
    const canvasContainer = document.querySelector('.slide-canvas-container')
    const slideElements = canvasContainer?.querySelectorAll('.slide-canvas') || 
                         document.querySelectorAll('.slide-canvas') ||
                         document.querySelectorAll('[data-slide-canvas]')
    
    if (slideElements.length === 0) {
      // 如果找不到画布元素，尝试查找编辑器中的幻灯片
      const editorSlides = document.querySelectorAll('.editor-slide-content') ||
                          document.querySelectorAll('.slide-content') ||
                          document.querySelectorAll('.canvas-slide')
      
      for (let i = 0; i < Math.min(editorSlides.length, slides.value.length); i++) {
        await exportSingleSlide(editorSlides[i] as HTMLElement, i)
      }
    }
    else {
      for (let i = 0; i < slideElements.length; i++) {
        await exportSingleSlide(slideElements[i] as HTMLElement, i)
      }
    }
  }

  /**
   * 导出单个幻灯片
   */
  const exportSingleSlide = async (slideElement: HTMLElement, index: number) => {
    try {
      // 等待渲染完成
      await new Promise(resolve => setTimeout(resolve, 200))

      // 转换为PNG图片
      const dataUrl = await toPng(slideElement, {
        width: 1920,
        height: 1080,
        style: {
          transform: 'scale(1)',
          transformOrigin: 'top left',
        },
        pixelRatio: 1,
        backgroundColor: '#ffffff',
      })

      // 将base64转换为blob并下载
      const response = await fetch(dataUrl)
      const blob = await response.blob()
      const fileName = `slide_${String(index + 1).padStart(3, '0')}.png`
      downloadFile(blob, fileName)

      // 短暂延迟避免浏览器阻止多文件下载
      await new Promise(resolve => setTimeout(resolve, 300))
      
    }
    catch (error) {
      // eslint-disable-next-line no-console
      console.error(`导出第${index + 1}页幻灯片失败:`, error)
      
      // 创建占位符图片
      const canvas = document.createElement('canvas')
      canvas.width = 1920
      canvas.height = 1080
      const ctx = canvas.getContext('2d')!
      
      // 绘制占位符
      ctx.fillStyle = '#f5f5f5'
      ctx.fillRect(0, 0, 1920, 1080)
      ctx.fillStyle = '#333'
      ctx.font = '48px Arial'
      ctx.textAlign = 'center'
      ctx.fillText(`幻灯片 ${index + 1}`, 960, 540)
      
      canvas.toBlob((blob) => {
        if (blob) {
          const fileName = `slide_${String(index + 1).padStart(3, '0')}.png`
          downloadFile(blob, fileName)
        }
      }, 'image/png')
    }
  }

  /**
   * 通用文件下载函数
   */
  const downloadFile = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  /**
   * 提取幻灯片标题
   */
  const extractSlideTitle = (slide: any): string => {
    // 查找文本元素作为标题
    const textElements = slide.elements?.filter((el: any) => el.type === 'text') || []
    
    if (textElements.length > 0) {
      // 取第一个文本元素作为标题，限制长度
      const firstText = textElements[0].content || ''
      const cleanText = firstText.replace(/<[^>]*>/g, '').trim() // 移除HTML标签
      return cleanText.length > 50 ? cleanText.substring(0, 50) + '...' : cleanText
    }
    
    return `幻灯片 ${slides.value.indexOf(slide) + 1}`
  }

  /**
   * 检查是否可以导出
   */
  const canExport = () => {
    return slides.value.length > 0
  }

  return {
    exporting,
    exportToOutputDirectory,
    canExport
  }
}
