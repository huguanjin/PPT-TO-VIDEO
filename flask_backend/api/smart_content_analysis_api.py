"""
任务4.2: 智能内容分析系统 - Flask API
提供RESTful API接口用于智能内容分析功能

API功能:
1. POST /api/content/analyze - 执行内容结构分析
2. GET /api/content/structure/{task_id} - 获取结构分析结果
3. POST /api/content/layout-recommendations - 生成布局推荐
4. POST /api/content/color-recommendations - 生成配色推荐
5. GET /api/content/summary/{task_id} - 获取分析摘要
6. POST /api/content/batch-analyze - 批量分析处理
7. GET /api/content/themes - 获取可用主题
8. POST /api/content/custom-analysis - 自定义分析参数

Author: Assistant
Date: 2025-09-09
Version: 1.0.0
"""
# type: ignore

from flask import Blueprint, request, jsonify
import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import logging

# 导入智能内容分析器 - 使用专门的导入模块解决路径问题
import sys
import os

# 确保当前目录在Python路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from analyzer_import import (
    get_smart_content_analyzer,
    get_content_types,
    get_importance_levels,
    get_layout_types,
    get_color_themes,
    get_logical_relations,
    is_import_successful
)

# 获取所需的类和枚举
SmartContentAnalyzer = get_smart_content_analyzer()
ContentType = get_content_types()
ImportanceLevel = get_importance_levels()
LayoutType = get_layout_types()
ColorTheme = get_color_themes()
LogicalRelation = get_logical_relations()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建蓝图
content_analysis_bp = Blueprint('content_analysis', __name__, url_prefix='/api/content')

# 全局存储分析结果和任务状态
analysis_results = {}
task_status = {}

# 线程池执行器
executor = ThreadPoolExecutor(max_workers=4)

def run_async_in_thread(coro):
    """在线程中运行异步函数"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@content_analysis_bp.route('/analyze', methods=['POST'])
def analyze_content():
    """执行内容结构分析"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请提供PPT数据'
            }), 400
        
        ppt_data = data.get('ppt_data')
        if not ppt_data:
            return jsonify({
                'success': False,
                'error': 'ppt_data字段不能为空'
            }), 400
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 记录任务状态
        task_status[task_id] = {
            'status': 'processing',
            'created_at': datetime.now().isoformat(),
            'progress': 0
        }
        
        # 异步执行分析
        def analyze_task():
            try:
                analyzer = SmartContentAnalyzer()
                
                # 更新进度
                task_status[task_id]['progress'] = 20
                
                # 执行内容结构分析
                structure = run_async_in_thread(analyzer.analyze_content_structure(ppt_data))
                task_status[task_id]['progress'] = 60
                
                # 生成推荐
                layout_recs = run_async_in_thread(analyzer.generate_layout_recommendations())
                task_status[task_id]['progress'] = 80
                
                color_recs = run_async_in_thread(analyzer.generate_color_recommendations())
                task_status[task_id]['progress'] = 100
                
                # 保存结果
                analysis_results[task_id] = {
                    'analyzer': analyzer,
                    'structure': structure,
                    'layout_recommendations': layout_recs,
                    'color_recommendations': color_recs,
                    'summary': analyzer.get_analysis_summary()
                }
                
                task_status[task_id]['status'] = 'completed'
                
            except Exception as e:
                logger.error(f"分析任务失败: {e}")
                task_status[task_id]['status'] = 'failed'
                task_status[task_id]['error'] = str(e)
        
        # 提交到线程池
        executor.submit(analyze_task)
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '内容分析任务已启动'
        })
        
    except Exception as e:
        logger.error(f"启动分析任务失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@content_analysis_bp.route('/structure/<task_id>', methods=['GET'])
def get_structure_analysis(task_id):
    """获取结构分析结果"""
    try:
        if task_id not in task_status:
            return jsonify({
                'success': False,
                'error': '任务ID不存在'
            }), 404
        
        status = task_status[task_id]['status']
        
        if status == 'processing':
            return jsonify({
                'success': True,
                'status': 'processing',
                'progress': task_status[task_id]['progress']
            })
        
        elif status == 'failed':
            return jsonify({
                'success': False,
                'status': 'failed',
                'error': task_status[task_id].get('error', '未知错误')
            })
        
        elif status == 'completed':
            if task_id not in analysis_results:
                return jsonify({
                    'success': False,
                    'error': '分析结果不存在'
                }), 404
            
            result = analysis_results[task_id]
            structure = result['structure']
            
            return jsonify({
                'success': True,
                'status': 'completed',
                'data': {
                    'slide_hierarchy': structure.slide_hierarchy,
                    'logical_flow': [rel.value for rel in structure.logical_flow],
                    'key_concepts': structure.key_concepts,
                    'content_density': structure.content_density,
                    'visual_balance': structure.visual_balance
                }
            })
        
    except Exception as e:
        logger.error(f"获取结构分析失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@content_analysis_bp.route('/layout-recommendations', methods=['POST'])
def get_layout_recommendations():
    """获取布局推荐"""
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        
        if not task_id or task_id not in analysis_results:
            return jsonify({
                'success': False,
                'error': '有效的task_id参数'
            }), 400
        
        result = analysis_results[task_id]
        layout_recs = result['layout_recommendations']
        
        recommendations = []
        for rec in layout_recs:
            recommendations.append({
                'slide_index': rec.slide_index,
                'recommended_layout': rec.recommended_layout.value,
                'confidence': rec.confidence,
                'reasoning': rec.reasoning,
                'adjustments': rec.adjustments
            })
        
        return jsonify({
            'success': True,
            'data': {
                'recommendations': recommendations,
                'total_count': len(recommendations)
            }
        })
        
    except Exception as e:
        logger.error(f"获取布局推荐失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@content_analysis_bp.route('/color-recommendations', methods=['POST'])
def get_color_recommendations():
    """获取配色推荐"""
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        
        if not task_id or task_id not in analysis_results:
            return jsonify({
                'success': False,
                'error': '需要有效的task_id参数'
            }), 400
        
        result = analysis_results[task_id]
        color_recs = result['color_recommendations']
        
        recommendations = []
        for rec in color_recs:
            recommendations.append({
                'theme': rec.theme.value,
                'primary_color': rec.primary_color,
                'secondary_color': rec.secondary_color,
                'accent_color': rec.accent_color,
                'background_color': rec.background_color,
                'text_color': rec.text_color,
                'confidence': rec.confidence,
                'reasoning': rec.reasoning
            })
        
        return jsonify({
            'success': True,
            'data': {
                'recommendations': recommendations,
                'total_count': len(recommendations)
            }
        })
        
    except Exception as e:
        logger.error(f"获取配色推荐失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@content_analysis_bp.route('/summary/<task_id>', methods=['GET'])
def get_analysis_summary(task_id):
    """获取分析摘要"""
    try:
        if task_id not in analysis_results:
            return jsonify({
                'success': False,
                'error': '任务ID不存在或分析未完成'
            }), 404
        
        result = analysis_results[task_id]
        summary = result['summary']
        
        return jsonify({
            'success': True,
            'data': {
                'summary': summary,
                'task_info': {
                    'task_id': task_id,
                    'created_at': task_status[task_id]['created_at'],
                    'status': task_status[task_id]['status']
                }
            }
        })
        
    except Exception as e:
        logger.error(f"获取分析摘要失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@content_analysis_bp.route('/batch-analyze', methods=['POST'])
def batch_analyze():
    """批量分析处理"""
    try:
        data = request.get_json()
        ppt_datasets = data.get('ppt_datasets', [])
        
        if not ppt_datasets:
            return jsonify({
                'success': False,
                'error': '请提供PPT数据集'
            }), 400
        
        # 生成批量任务ID
        batch_id = str(uuid.uuid4())
        task_ids = []
        
        # 为每个PPT数据创建分析任务
        for i, ppt_data in enumerate(ppt_datasets):
            task_id = f"{batch_id}_{i}"
            task_ids.append(task_id)
            
            # 记录任务状态
            task_status[task_id] = {
                'status': 'processing',
                'created_at': datetime.now().isoformat(),
                'progress': 0,
                'batch_id': batch_id
            }
            
            # 异步执行分析
            def analyze_batch_task(tid, data):
                try:
                    analyzer = SmartContentAnalyzer()
                    structure = run_async_in_thread(analyzer.analyze_content_structure(data))
                    layout_recs = run_async_in_thread(analyzer.generate_layout_recommendations())
                    color_recs = run_async_in_thread(analyzer.generate_color_recommendations())
                    
                    analysis_results[tid] = {
                        'analyzer': analyzer,
                        'structure': structure,
                        'layout_recommendations': layout_recs,
                        'color_recommendations': color_recs,
                        'summary': analyzer.get_analysis_summary()
                    }
                    
                    task_status[tid]['status'] = 'completed'
                    task_status[tid]['progress'] = 100
                    
                except Exception as e:
                    logger.error(f"批量分析任务{tid}失败: {e}")
                    task_status[tid]['status'] = 'failed'
                    task_status[tid]['error'] = str(e)
            
            executor.submit(analyze_batch_task, task_id, ppt_data)
        
        return jsonify({
            'success': True,
            'batch_id': batch_id,
            'task_ids': task_ids,
            'message': f'批量分析任务已启动，共{len(task_ids)}个任务'
        })
        
    except Exception as e:
        logger.error(f"启动批量分析失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@content_analysis_bp.route('/themes', methods=['GET'])
def get_available_themes():
    """获取可用主题"""
    try:
        themes = []
        for theme in ColorTheme:
            themes.append({
                'value': theme.value,
                'name': theme.value,
                'description': f'{theme.value}主题配色方案'
            })
        
        layout_types = []
        for layout in LayoutType:
            layout_types.append({
                'value': layout.value,
                'name': layout.value,
                'description': f'{layout.value}布局类型'
            })
        
        content_types = []
        for ctype in ContentType:
            content_types.append({
                'value': ctype.value,
                'name': ctype.value,
                'description': f'{ctype.value}内容类型'
            })
        
        return jsonify({
            'success': True,
            'data': {
                'color_themes': themes,
                'layout_types': layout_types,
                'content_types': content_types,
                'importance_levels': [level.value for level in ImportanceLevel],
                'logical_relations': [rel.value for rel in LogicalRelation]
            }
        })
        
    except Exception as e:
        logger.error(f"获取可用主题失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@content_analysis_bp.route('/custom-analysis', methods=['POST'])
def custom_analysis():
    """自定义分析参数"""
    try:
        data = request.get_json()
        ppt_data = data.get('ppt_data')
        analysis_config = data.get('analysis_config', {})
        
        if not ppt_data:
            return jsonify({
                'success': False,
                'error': 'ppt_data字段不能为空'
            }), 400
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 记录任务状态
        task_status[task_id] = {
            'status': 'processing',
            'created_at': datetime.now().isoformat(),
            'progress': 0,
            'custom_config': analysis_config
        }
        
        def custom_analyze_task():
            try:
                analyzer = SmartContentAnalyzer()
                
                # 应用自定义配置
                if 'keyword_weights' in analysis_config:
                    analyzer.keyword_weights.update(analysis_config['keyword_weights'])
                
                if 'color_psychology' in analysis_config:
                    analyzer.color_psychology.update(analysis_config['color_psychology'])
                
                # 执行分析
                structure = run_async_in_thread(analyzer.analyze_content_structure(ppt_data))
                
                # 根据配置决定是否生成推荐
                layout_recs = []
                color_recs = []
                
                if analysis_config.get('generate_layout_recommendations', True):
                    layout_recs = run_async_in_thread(analyzer.generate_layout_recommendations())
                
                if analysis_config.get('generate_color_recommendations', True):
                    color_recs = run_async_in_thread(analyzer.generate_color_recommendations())
                
                # 保存结果
                analysis_results[task_id] = {
                    'analyzer': analyzer,
                    'structure': structure,
                    'layout_recommendations': layout_recs,
                    'color_recommendations': color_recs,
                    'summary': analyzer.get_analysis_summary(),
                    'custom_config': analysis_config
                }
                
                task_status[task_id]['status'] = 'completed'
                task_status[task_id]['progress'] = 100
                
            except Exception as e:
                logger.error(f"自定义分析任务失败: {e}")
                task_status[task_id]['status'] = 'failed'
                task_status[task_id]['error'] = str(e)
        
        executor.submit(custom_analyze_task)
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '自定义分析任务已启动',
            'config': analysis_config
        })
        
    except Exception as e:
        logger.error(f"启动自定义分析失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@content_analysis_bp.route('/status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """获取任务状态"""
    try:
        if task_id not in task_status:
            return jsonify({
                'success': False,
                'error': '任务ID不存在'
            }), 404
        
        status = task_status[task_id]
        
        return jsonify({
            'success': True,
            'data': {
                'task_id': task_id,
                'status': status['status'],
                'progress': status['progress'],
                'created_at': status['created_at'],
                'error': status.get('error'),
                'batch_id': status.get('batch_id'),
                'custom_config': status.get('custom_config')
            }
        })
        
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@content_analysis_bp.route('/cleanup', methods=['POST'])
def cleanup_results():
    """清理过期结果"""
    try:
        data = request.get_json()
        task_ids = data.get('task_ids', [])
        
        cleaned_count = 0
        
        if task_ids:
            # 清理指定任务
            for task_id in task_ids:
                if task_id in analysis_results:
                    del analysis_results[task_id]
                if task_id in task_status:
                    del task_status[task_id]
                cleaned_count += 1
        else:
            # 清理所有完成的任务
            completed_tasks = [
                tid for tid, status in task_status.items() 
                if status['status'] in ['completed', 'failed']
            ]
            
            for task_id in completed_tasks:
                if task_id in analysis_results:
                    del analysis_results[task_id]
                if task_id in task_status:
                    del task_status[task_id]
                cleaned_count += 1
        
        return jsonify({
            'success': True,
            'message': f'清理了{cleaned_count}个任务结果',
            'cleaned_count': cleaned_count
        })
        
    except Exception as e:
        logger.error(f"清理结果失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# API文档端点
@content_analysis_bp.route('/docs', methods=['GET'])
def api_documentation():
    """API文档"""
    docs = {
        'title': '智能内容分析系统 API',
        'version': '1.0.0',
        'description': '提供PPT内容智能分析、布局推荐、配色建议等功能',
        'endpoints': {
            'POST /api/content/analyze': {
                'description': '执行内容结构分析',
                'parameters': {
                    'ppt_data': '必需，PPT数据对象'
                },
                'returns': 'task_id 用于查询结果'
            },
            'GET /api/content/structure/<task_id>': {
                'description': '获取结构分析结果',
                'parameters': {
                    'task_id': '必需，分析任务ID'
                },
                'returns': '内容结构分析数据'
            },
            'POST /api/content/layout-recommendations': {
                'description': '获取布局推荐',
                'parameters': {
                    'task_id': '必需，分析任务ID'
                },
                'returns': '布局推荐列表'
            },
            'POST /api/content/color-recommendations': {
                'description': '获取配色推荐',
                'parameters': {
                    'task_id': '必需，分析任务ID'
                },
                'returns': '配色推荐列表'
            },
            'GET /api/content/summary/<task_id>': {
                'description': '获取分析摘要',
                'parameters': {
                    'task_id': '必需，分析任务ID'
                },
                'returns': '分析结果摘要'
            },
            'POST /api/content/batch-analyze': {
                'description': '批量分析处理',
                'parameters': {
                    'ppt_datasets': '必需，PPT数据集数组'
                },
                'returns': 'batch_id 和 task_ids'
            },
            'GET /api/content/themes': {
                'description': '获取可用主题和类型',
                'parameters': {},
                'returns': '主题、布局类型等枚举值'
            },
            'POST /api/content/custom-analysis': {
                'description': '自定义分析参数',
                'parameters': {
                    'ppt_data': '必需，PPT数据对象',
                    'analysis_config': '可选，自定义分析配置'
                },
                'returns': 'task_id 用于查询结果'
            }
        }
    }
    
    return jsonify(docs)

# 健康检查端点
@content_analysis_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'success': True,
        'service': '智能内容分析系统',
        'status': 'healthy',
        'active_tasks': len([t for t in task_status.values() if t['status'] == 'processing']),
        'total_results': len(analysis_results),
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    # 用于测试的简单Flask应用
    from flask import Flask
    
    app = Flask(__name__)
    app.register_blueprint(content_analysis_bp)
    
    print("🧠 智能内容分析API服务器启动")
    print("=" * 50)
    print("API端点:")
    print("POST /api/content/analyze - 执行内容分析")
    print("GET  /api/content/structure/<task_id> - 获取结构分析")
    print("POST /api/content/layout-recommendations - 获取布局推荐")
    print("POST /api/content/color-recommendations - 获取配色推荐")
    print("GET  /api/content/themes - 获取可用主题")
    print("GET  /api/content/docs - API文档")
    print("GET  /api/content/health - 健康检查")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=8002)
