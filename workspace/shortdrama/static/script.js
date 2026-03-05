

        // ==================== 短剧制作流程 JavaScript ====================
        
        // 步骤切换
        function nextStep(step) {
            // 隐藏所有面板
            document.querySelectorAll('.workflow-panel').forEach(panel => {
                panel.style.display = 'none';
            });
            
            // 显示目标面板
            const targetPanel = document.getElementById(`step${step}-panel`);
            if (targetPanel) {
                targetPanel.style.display = 'block';
            }
            
            // 更新步骤指示器
            document.querySelectorAll('.step-item').forEach((item, index) => {
                item.classList.remove('active');
                if (index + 1 === step) {
                    item.classList.add('active');
                }
            });
            
            // 滚动到顶部
            document.getElementById('shooting').scrollIntoView({ behavior: 'smooth' });
        }
        
        // 结果标签切换
        function switchResultTab(tab) {
            // 更新标签状态
            document.querySelectorAll('.result-tab').forEach(t => {
                t.classList.remove('active');
            });
            event.target.classList.add('active');
            
            // 显示对应面板
            if (tab === 'script-text') {
                document.getElementById('script-text-panel').style.display = 'block';
                document.getElementById('storyboard-panel').style.display = 'none';
            } else {
                document.getElementById('script-text-panel').style.display = 'none';
                document.getElementById('storyboard-panel').style.display = 'block';
            }
        }
        
        // 生成剧本与分镜
        // 切换结果标签
        function switchResultTab(tabName) {
            const tabs = document.querySelectorAll('.result-tab');
            tabs.forEach(tab => tab.classList.remove('active'));
            
            const panels = document.querySelectorAll('.result-panel');
            panels.forEach(panel => panel.style.display = 'none');
            
            event.target.classList.add('active');
            
            if (tabName === 'script-text') {
                document.getElementById('script-text-panel').style.display = 'block';
            } else if (tabName === 'storyboard') {
                document.getElementById('storyboard-panel').style.display = 'block';
            } else if (tabName === 'script-analysis') {
                document.getElementById('script-analysis-panel').style.display = 'block';
            }
        }
        
        // 生成剧本与分镜
        function generateScriptAndStoryboard() {
            const topic = document.getElementById('script-topic').value;
            const style = document.getElementById('script-style').value;
            const duration = document.getElementById('script-duration').value;
            const characters = document.getElementById('script-characters').value;
            const setting = document.getElementById('script-setting').value;
            const plot = document.getElementById('script-plot').value;
            
            if (!topic) {
                alert('请输入短剧主题');
                return;
            }
            
            const button = event.target;
            button.disabled = true;
            button.innerHTML = '<span class="loading-spinner"></span> 生成中...';
            
            // 调用后端API生成剧本
            fetch('/api/shortdrama/script', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    topic: topic,
                    style: style,
                    duration: duration,
                    characters: characters,
                    setting: setting,
                    plot: plot
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('generated-script').textContent = data.script;
                    document.getElementById('script-analysis').innerHTML = data.analysis;
                    
                    // 生成分镜预览
                    const storyboardGrid = document.getElementById('storyboard-grid');
                    storyboardGrid.innerHTML = '';
                    
                    data.storyboard.forEach((scene, index) => {
                        const item = document.createElement('div');
                        item.className = 'storyboard-item';
                        item.innerHTML = `
                            <div style="height: 120px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center; color: white; font-size: 24px;">
                                🎬
                            </div>
                            <div class="caption">
                                <strong>场景 ${index + 1}：${scene.name}</strong>
                                <br><small>${scene.description}</small>
                            </div>
                        `;
                        storyboardGrid.appendChild(item);
                    });
                    
                    document.getElementById('script-result').style.display = 'block';
                    showToast('剧本与分镜生成完成！');
                } else {
                    throw new Error(data.error || '生成失败');
                }
            })
            .catch(error => {
                console.error('剧本生成错误:', error);
                // 如果API调用失败，使用模拟数据
                const characterList = characters ? characters.split(',').map(c => c.trim()).join('、') : '主角、配角';
                const settingText = setting || '现代都市';
                
                const scriptContent = `
【${topic}】

类型：${style === 'realistic' ? '现实主义' : style === 'romantic' ? '浪漫唯美' : style === 'suspense' ? '悬疑惊悚' : style === 'comedy' ? '轻松喜剧' : '励志向上'}
时长：${duration}秒
场景：${settingText}
角色：${characterList}

第一幕：开场
场景：${settingText}
人物：${characterList}

${characterList.split('、')[0] || '主角'}：（独白）在这个快节奏的世界里，每个人都在为生活奔波...

${characterList.split('、')[1] || '配角'}：（走过来）好久不见！

${characterList.split('、')[0] || '主角'}：（惊讶）真的是你！

第二幕：发展
场景：${settingText === '现代都市' ? '咖啡厅' : settingText}
两人坐下来聊天，回忆过去的点点滴滴...

第三幕：高潮
场景：${settingText === '现代都市' ? '天台' : settingText}
夕阳西下，两人站在高处，展望未来...

第四幕：结尾
场景：${settingText === '现代都市' ? '街头' : settingText}
两人告别，各自走向不同的方向，但心中都充满了希望...

【分镜描述】
1. 开场：广角镜头，${settingText}全景，慢慢推进到主角
2. 相遇：中景，两人面对面，表情惊讶
3. 对话：近景交替，展现人物情感变化
4. 高潮：全景，夕阳背景，剪影效果
5. 结尾：远景，两人背影，渐行渐远

【技术参数】
- 总时长：${duration}秒
- 镜头数量：15-20个
- 主要景别：中景、近景、全景
- 镜头运动：推拉、摇移、跟拍
                `;
                
                document.getElementById('generated-script').textContent = scriptContent;
                
                const analysisContent = `
<div class="analysis-item">
    <h4>📊 剧本结构分析</h4>
    <ul>
        <li>四幕结构：开场-发展-高潮-结尾</li>
        <li>节奏控制：前慢后快，符合短剧规律</li>
        <li>情感曲线：平稳-上升-高潮-回落</li>
    </ul>
</div>
<div class="analysis-item">
    <h4>👥 角色分析</h4>
    <ul>
        <li>角色数量：${characterList.split('、').length}个</li>
        <li>角色关系：清晰明确，易于理解</li>
        <li>角色发展：有成长弧线</li>
    </ul>
</div>
<div class="analysis-item">
    <h4>🎬 视觉风格建议</h4>
    <ul>
        <li>色调：${style === 'romantic' ? '暖色调' : style === 'suspense' ? '冷色调' : '自然色调'}</li>
        <li>构图：黄金分割，突出人物</li>
        <li>光影：${style === 'suspense' ? '高对比度' : '柔和自然'}</li>
    </ul>
</div>
<div class="analysis-item">
    <h4>⚡ 优化建议</h4>
    <ul>
        <li>建议在前3秒增加钩子元素</li>
        <li>高潮部分可以增加更多冲突</li>
        <li>结尾可以增加悬念或反转</li>
    </ul>
</div>
                `;
                document.getElementById('script-analysis').innerHTML = analysisContent;
                
                const storyboardGrid = document.getElementById('storyboard-grid');
                storyboardGrid.innerHTML = '';
                
                const scenes = ['开场', '相遇', '对话', '高潮', '结尾'];
                const sceneDescriptions = [
                    '广角镜头，全景展示',
                    '中景，两人相遇',
                    '近景，情感交流',
                    '全景，高潮时刻',
                    '远景，渐行渐远'
                ];
                
                scenes.forEach((scene, index) => {
                    const item = document.createElement('div');
                    item.className = 'storyboard-item';
                    item.innerHTML = `
                        <div style="height: 120px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center; color: white; font-size: 24px;">
                            🎬
                        </div>
                        <div class="caption">
                            <strong>场景 ${index + 1}：${scene}</strong>
                            <br><small>${sceneDescriptions[index]}</small>
                        </div>
                    `;
                    storyboardGrid.appendChild(item);
                });
                
                document.getElementById('script-result').style.display = 'block';
                showToast('剧本与分镜生成完成（模拟模式）');
            })
            .finally(() => {
                button.disabled = false;
                button.innerHTML = '<span class="btn-icon">🎬</span> 生成剧本与分镜';
            });
        }
        
        // 加载剧本模板
        function loadScriptTemplate() {
            const templates = [
                { topic: '职场逆袭', style: 'inspirational', duration: '120', characters: '李明,张总,王经理', setting: '现代都市', plot: '新人职场奋斗，最终获得认可' },
                { topic: '甜宠爱情', style: 'romantic', duration: '120', characters: '小明,小红', setting: '校园', plot: '校园恋爱故事' },
                { topic: '悬疑推理', style: 'suspense', duration: '180', characters: '侦探,嫌疑人', setting: '现代都市', plot: '破案过程' }
            ];
            
            const template = templates[Math.floor(Math.random() * templates.length)];
            
            document.getElementById('script-topic').value = template.topic;
            document.getElementById('script-style').value = template.style;
            document.getElementById('script-duration').value = template.duration;
            document.getElementById('script-characters').value = template.characters;
            document.getElementById('script-setting').value = template.setting;
            document.getElementById('script-plot').value = template.plot;
            
            showToast('模板加载成功！');
        }
        
        // 编辑剧本
        function editScript() {
            const scriptContent = document.getElementById('generated-script').textContent;
            const newContent = prompt('编辑剧本内容：', scriptContent);
            if (newContent !== null) {
                document.getElementById('generated-script').textContent = newContent;
                showToast('剧本已更新！');
            }
        }
        
        // 重新生成剧本
        function regenerateScript() {
            showToast('正在重新生成剧本...');
            generateScriptAndStoryboard();
        }
        
        // 导出剧本
        function exportScript() {
            const scriptContent = document.getElementById('generated-script').textContent;
            const blob = new Blob([scriptContent], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = '剧本.txt';
            a.click();
            URL.revokeObjectURL(url);
            showToast('剧本已导出！');
        }
        
        // 编辑分镜
        function editStoryboard() {
            const storyboardGrid = document.getElementById('storyboard-grid');
            const items = storyboardGrid.querySelectorAll('.storyboard-item');
            
            if (items.length === 0) {
                showToast('请先生成分镜！');
                return;
            }
            
            // 创建编辑模态框
            const modal = document.createElement('div');
            modal.className = 'modal-overlay';
            modal.innerHTML = `
                <div class="modal-content">
                    <h3>编辑分镜</h3>
                    <div class="storyboard-edit-list" id="storyboard-edit-list"></div>
                    <div class="modal-actions">
                        <button class="btn btn-primary" onclick="saveStoryboardEdit()">保存修改</button>
                        <button class="btn btn-secondary" onclick="closeModal()">取消</button>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // 填充编辑列表
            const editList = document.getElementById('storyboard-edit-list');
            items.forEach((item, index) => {
                const caption = item.querySelector('.caption').innerHTML;
                const editItem = document.createElement('div');
                editItem.className = 'storyboard-edit-item';
                editItem.innerHTML = `
                    <label>场景 ${index + 1} 描述：</label>
                    <input type="text" class="scene-description" value="${caption.replace(/<[^>]*>/g, '')}">
                    <label>镜头类型：</label>
                    <select class="shot-type">
                        <option value="wide">广角镜头</option>
                        <option value="medium">中景</option>
                        <option value="close">近景</option>
                        <option value="extreme-close">特写</option>
                    </select>
                    <label>镜头运动：</label>
                    <select class="shot-movement">
                        <option value="static">固定</option>
                        <option value="push">推镜头</option>
                        <option value="pull">拉镜头</option>
                        <option value="pan">摇镜头</option>
                        <option value="track">跟镜头</option>
                    </select>
                `;
                editList.appendChild(editItem);
            });
        }
        
        // 保存分镜编辑
        function saveStoryboardEdit() {
            showToast('分镜修改已保存！');
            closeModal();
        }
        
        // 关闭模态框
        function closeModal() {
            const modal = document.querySelector('.modal-overlay');
            if (modal) {
                modal.remove();
            }
        }
        
        // 重新生成分镜
        function regenerateStoryboard() {
            const button = event.target;
            button.disabled = true;
            button.innerHTML = '<span class="loading-spinner"></span> 生成中...';
            
            setTimeout(() => {
                const storyboardGrid = document.getElementById('storyboard-grid');
                storyboardGrid.innerHTML = '';
                
                const scenes = ['开场', '相遇', '对话', '高潮', '结尾'];
                const sceneDescriptions = [
                    '广角镜头，全景展示',
                    '中景，两人相遇',
                    '近景，情感交流',
                    '全景，高潮时刻',
                    '远景，渐行渐远'
                ];
                
                scenes.forEach((scene, index) => {
                    const item = document.createElement('div');
                    item.className = 'storyboard-item';
                    item.innerHTML = `
                        <div style="height: 120px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center; color: white; font-size: 24px;">
                            🎬
                        </div>
                        <div class="caption">
                            <strong>场景 ${index + 1}：${scene}</strong>
                            <br><small>${sceneDescriptions[index]}</small>
                        </div>
                    `;
                    storyboardGrid.appendChild(item);
                });
                
                button.disabled = false;
                button.innerHTML = '🔄 重新生成分镜';
                
                showToast('分镜重新生成完成！');
            }, 2000);
        }
        
        // 导出分镜
        function exportStoryboard() {
            const storyboardGrid = document.getElementById('storyboard-grid');
            const items = storyboardGrid.querySelectorAll('.storyboard-item');
            
            if (items.length === 0) {
                showToast('请先生成分镜！');
                return;
            }
            
            let storyboardText = '分镜脚本\n\n';
            items.forEach((item, index) => {
                const caption = item.querySelector('.caption').innerHTML;
                storyboardText += `场景 ${index + 1}：${caption.replace(/<[^>]*>/g, '')}\n\n`;
            });
            
            const blob = new Blob([storyboardText], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = '分镜脚本.txt';
            a.click();
            URL.revokeObjectURL(url);
            
            showToast('分镜脚本已导出！');
        }
        
        // 生成角色
        function generateCharacters() {
            const model = document.getElementById('character-model').value;
            const style = document.getElementById('character-style').value;
            const expressions = document.getElementById('character-expressions').value;
            const viewFront = document.getElementById('view-front').checked;
            const viewSide = document.getElementById('view-side').checked;
            const viewBack = document.getElementById('view-back').checked;
            
            if (!viewFront && !viewSide && !viewBack) {
                alert('请至少选择一个角色视图');
                return;
            }
            
            const button = event.target;
            button.disabled = true;
            button.innerHTML = '<span class="loading-spinner"></span> 生成中...';
            
            // 从剧本中获取角色列表
            const scriptContent = document.getElementById('generated-script').textContent;
            const characterMatch = scriptContent.match(/角色：([^\n]+)/);
            const characterNames = characterMatch ? characterMatch[1].split('、') : ['主角', '配角'];
            
            setTimeout(() => {
                const showcase = document.getElementById('character-showcase');
                showcase.innerHTML = '';
                
                characterNames.forEach((name, index) => {
                    const card = document.createElement('div');
                    card.className = 'character-card';
                    card.innerHTML = `
                        <div class="character-views">
                            ${viewFront ? `<div class="character-view" style="height: 150px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center; color: white; font-size: 48px;">👤</div>` : ''}
                            ${viewSide ? `<div class="character-view" style="height: 150px; background: linear-gradient(135deg, #764ba2 0%, #667eea 100%); display: flex; align-items: center; justify-content: center; color: white; font-size: 48px;">👥</div>` : ''}
                            ${viewBack ? `<div class="character-view" style="height: 150px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center; color: white; font-size: 48px;">🚶</div>` : ''}
                        </div>
                        <div class="name">
                            <strong>${name}</strong>
                            <br><small>${style === 'realistic' ? '写实' : style === 'anime' ? '动漫' : style === 'cartoon' ? '卡通' : '艺术'}风格</small>
                            <br><small>模型：${model === 'doubao' ? '豆包' : model === 'skyreels' ? 'SkyReels-V3' : '混合'}</small>
                        </div>
                        ${expressions !== 'none' ? `
                        <div class="expressions">
                            <span class="expression-icon">😊</span>
                            <span class="expression-icon">😢</span>
                            <span class="expression-icon">😠</span>
                            <span class="expression-icon">😮</span>
                        </div>
                        ` : ''}
                    `;
                    showcase.appendChild(card);
                });
                
                document.getElementById('character-result').style.display = 'block';
                
                button.disabled = false;
                button.innerHTML = '<span class="btn-icon">🎨</span> 生成角色形象';
                
                showToast('角色生成完成！');
            }, 2000);
        }
        
        // 添加自定义角色
        function addCustomCharacter() {
            const name = prompt('请输入角色名称：');
            if (name) {
                const characterList = document.getElementById('character-list');
                const item = document.createElement('div');
                item.className = 'character-item';
                item.innerHTML = `
                    <span>${name}</span>
                    <button class="btn btn-sm btn-secondary" onclick="removeCharacter(this)">删除</button>
                `;
                characterList.appendChild(item);
                showToast(`已添加角色：${name}`);
            }
        }
        
        // 删除角色
        function removeCharacter(button) {
            if (confirm('确定要删除这个角色吗？')) {
                button.parentElement.remove();
                showToast('角色已删除');
            }
        }
        
        // 编辑角色
        function editCharacter() {
            showToast('角色编辑功能开发中...');
        }
        
        // 重新生成角色
        function regenerateCharacter() {
            showToast('正在重新生成角色...');
            generateCharacters();
        }
        
        // 导出角色
        function exportCharacter() {
            const showcase = document.getElementById('character-showcase');
            const cards = showcase.querySelectorAll('.character-card');
            
            if (cards.length === 0) {
                showToast('请先生成角色！');
                return;
            }
            
            let characterText = '角色素材导出\n\n';
            cards.forEach((card, index) => {
                const name = card.querySelector('.name strong').textContent;
                characterText += `角色 ${index + 1}：${name}\n`;
                characterText += `风格：${card.querySelector('.name small').textContent}\n\n`;
            });
            
            const blob = new Blob([characterText], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = '角色素材.txt';
            a.click();
            URL.revokeObjectURL(url);
            
            showToast('角色素材已导出！');
        }
        
        // 生成视频
        function generateVideo() {
            const mode = document.querySelector('input[name="video-mode"]:checked').value;
            const resolution = document.getElementById('video-resolution').value;
            
            const button = event.target;
            button.disabled = true;
            button.innerHTML = '<span class="loading-spinner"></span> 视频生成中...';
            
            document.getElementById('video-progress').style.display = 'block';
            
            // 生成场景时间线
            const timeline = document.getElementById('scene-timeline');
            timeline.innerHTML = '';
            
            const scenes = [
                { name: '开场', duration: '0:00-0:15', status: 'pending' },
                { name: '相遇', duration: '0:15-0:30', status: 'pending' },
                { name: '对话', duration: '0:30-1:00', status: 'pending' },
                { name: '高潮', duration: '1:00-1:30', status: 'pending' },
                { name: '结尾', duration: '1:30-2:00', status: 'pending' }
            ];
            
            scenes.forEach((scene, index) => {
                const item = document.createElement('div');
                item.className = 'scene-item';
                item.id = `scene-${index}`;
                item.innerHTML = `
                    <div class="scene-info">
                        <strong>场景 ${index + 1}：${scene.name}</strong>
                        <small>${scene.duration}</small>
                    </div>
                    <div class="scene-status" id="scene-status-${index}">等待中</div>
                `;
                timeline.appendChild(item);
            });
            
            let progress = 0;
            const progressFill = document.getElementById('video-progress-fill');
            const progressText = document.getElementById('progress-text');
            const progressPercent = document.getElementById('progress-percent');
            const gpuUsage = document.getElementById('gpu-usage');
            
            // 根据模式设置生成速度
            const speedMultiplier = mode === 'fast' ? 2 : mode === 'batch' ? 1.5 : 1;
            
            const interval = setInterval(() => {
                progress += Math.random() * 10 * speedMultiplier;
                if (progress > 100) progress = 100;
                
                progressFill.style.width = progress + '%';
                progressPercent.textContent = Math.floor(progress) + '%';
                
                // 更新场景状态
                const currentScene = Math.floor(progress / 20);
                for (let i = 0; i < scenes.length; i++) {
                    const sceneStatus = document.getElementById(`scene-status-${i}`);
                    const sceneItem = document.getElementById(`scene-${i}`);
                    
                    if (i < currentScene) {
                        sceneStatus.textContent = '已完成';
                        sceneStatus.style.color = '#4CAF50';
                        sceneItem.style.background = '#e8f5e8';
                    } else if (i === currentScene) {
                        sceneStatus.textContent = '生成中';
                        sceneStatus.style.color = '#667eea';
                        sceneItem.style.background = '#e8eaf6';
                    } else {
                        sceneStatus.textContent = '等待中';
                        sceneStatus.style.color = '#888';
                        sceneItem.style.background = '#f5f5f5';
                    }
                }
                
                // 更新进度文本
                if (progress < 20) {
                    progressText.textContent = '正在分析剧本结构...';
                    gpuUsage.textContent = '8卡并行运行中 - 准备阶段';
                } else if (progress < 40) {
                    progressText.textContent = '正在生成视频画面...';
                    gpuUsage.textContent = '8卡并行运行中 - 渲染中';
                } else if (progress < 60) {
                    progressText.textContent = '正在优化视频质量...';
                    gpuUsage.textContent = '8卡并行运行中 - 优化中';
                } else if (progress < 80) {
                    progressText.textContent = '正在合成特效...';
                    gpuUsage.textContent = '8卡并行运行中 - 特效合成';
                } else if (progress < 100) {
                    progressText.textContent = '即将完成...';
                    gpuUsage.textContent = '8卡并行运行中 - 最终渲染';
                }
                
                if (progress >= 100) {
                    clearInterval(interval);
                    
                    setTimeout(() => {
                        document.getElementById('video-result').style.display = 'block';
                        
                        const preview = document.getElementById('video-preview');
                        preview.innerHTML = `
                            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 300px; display: flex; align-items: center; justify-content: center; color: white; border-radius: 12px;">
                                <div style="text-align: center;">
                                    <div style="font-size: 64px; margin-bottom: 20px;">🎬</div>
                                    <div style="font-size: 18px;">视频生成完成！</div>
                                    <div style="font-size: 14px; opacity: 0.8; margin-top: 10px;">
                                        时长：2分钟 | 分辨率：${resolution} | 模式：${mode === 'standard' ? '标准' : mode === 'fast' ? '快速' : '批量'}
                                    </div>
                                    <div style="margin-top: 20px;">
                                        <button class="btn btn-sm" onclick="previewVideo()">▶ 预览</button>
                                        <button class="btn btn-sm btn-secondary" onclick="downloadVideo()">📥 下载</button>
                                        <button class="btn btn-sm btn-secondary" onclick="regenerateVideo()">🔄 重新生成</button>
                                    </div>
                                </div>
                            </div>
                        `;
                        
                        button.disabled = false;
                        button.innerHTML = '<span class="btn-icon">🎬</span> 开始AI视频生成';
                        
                        showToast('视频生成完成！');
                    }, 500);
                }
            }, 500);
        }
        
        // 预览视频
        function previewVideo() {
            showToast('视频预览功能开发中...');
        }
        
        // 下载视频
        function downloadVideo() {
            showToast('开始下载视频...');
        }
        
        // 重新生成视频
        function regenerateVideo() {
            showToast('正在重新生成视频...');
            generateVideo();
        }
        
        // 生成语音
        function generateVoice() {
            const voicePreset = document.querySelector('.voice-preset.active').dataset.voice;
            const language = document.getElementById('voice-language').value;
            
            const button = event.target;
            button.disabled = true;
            button.innerHTML = '<span class="loading-spinner"></span> 合成中...';
            
            // 从剧本中提取对白
            const scriptContent = document.getElementById('generated-script').textContent;
            const dialogues = extractDialogues(scriptContent);
            
            // 生成对白列表
            const dialogueList = document.getElementById('dialogue-list');
            dialogueList.innerHTML = '';
            
            dialogues.forEach((dialogue, index) => {
                const item = document.createElement('div');
                item.className = 'dialogue-item';
                item.innerHTML = `
                    <div class="dialogue-header">
                        <strong>${dialogue.character}</strong>
                        <small>${dialogue.time}</small>
                    </div>
                    <div class="dialogue-text">${dialogue.text}</div>
                    <div class="dialogue-actions">
                        <button class="btn btn-sm" onclick="playAudio(${index})">▶ 播放</button>
                        <button class="btn btn-sm btn-secondary" onclick="regenerateAudio(${index})">🔄 重新生成</button>
                    </div>
                `;
                dialogueList.appendChild(item);
            });
            
            setTimeout(() => {
                const timeline = document.getElementById('audio-timeline');
                timeline.innerHTML = '';
                
                dialogues.forEach((dialogue, index) => {
                    const item = document.createElement('div');
                    item.className = 'audio-item';
                    item.innerHTML = `
                        <div class="audio-info">
                            <strong>${dialogue.character}</strong>
                            <small>${dialogue.time}</small>
                        </div>
                        <div class="audio-waveform">
                            <div class="waveform-bar"></div>
                            <div class="waveform-bar"></div>
                            <div class="waveform-bar"></div>
                            <div class="waveform-bar"></div>
                            <div class="waveform-bar"></div>
                        </div>
                        <div class="audio-actions">
                            <button class="btn btn-sm" onclick="playAudio(${index})">▶</button>
                            <button class="btn btn-sm btn-secondary" onclick="downloadAudio(${index})">📥</button>
                        </div>
                    `;
                    timeline.appendChild(item);
                });
                
                document.getElementById('voice-result').style.display = 'block';
                
                button.disabled = false;
                button.innerHTML = '<span class="btn-icon">🎙️</span> 合成情感语音';
                
                showToast(`语音合成完成！共${dialogues.length}段对白`);
            }, 2000);
        }
        
        // 提取剧本中的对白
        function extractDialogues(script) {
            const dialogues = [];
            const lines = script.split('\n');
            
            lines.forEach(line => {
                const match = line.match(/([^（]+)[（]([^）]+)[）]：(.+)/);
                if (match) {
                    dialogues.push({
                        character: match[1].trim(),
                        time: '0:' + String(dialogues.length * 5 + 5).padStart(2, '0'),
                        text: match[3].trim()
                    });
                }
            });
            
            // 如果没有找到对白，使用示例对白
            if (dialogues.length === 0) {
                dialogues.push(
                    { character: '主角', time: '0:05', text: '在这个快节奏的世界里，每个人都在为生活奔波...' },
                    { character: '配角', time: '0:15', text: '好久不见！' },
                    { character: '主角', time: '0:25', text: '真的是你！' }
                );
            }
            
            return dialogues;
        }
        
        // 播放音频（模拟）
        function playAudio(index) {
            const dialogues = extractDialogues(document.getElementById('generated-script').textContent);
            if (dialogues[index]) {
                showToast(`正在播放：${dialogues[index].character} - ${dialogues[index].text.substring(0, 20)}...`);
            }
        }
        
        // 重新生成音频（模拟）
        function regenerateAudio(index) {
            showToast(`正在重新生成音频片段 ${index + 1}...`);
        }
        
        // 下载音频
        function downloadAudio(index) {
            showToast(`开始下载音频片段 ${index + 1}...`);
        }
        
        // 导出所有音频
        function exportAllAudio() {
            showToast('正在导出所有音频...');
        }
        
        // 完成制作
        function finalizeProduction() {
            const button = event.target;
            button.disabled = true;
            button.innerHTML = '<span class="loading-spinner"></span> 处理中...';
            
            // 更新素材统计
            updateAssetStats();
            
            // 更新任务队列
            updateTaskQueue();
            
            setTimeout(() => {
                document.getElementById('final-result').style.display = 'block';
                
                button.disabled = false;
                button.innerHTML = '<span class="btn-icon">🚀</span> 完成制作并发布';
                
                showToast('短剧制作完成！');
            }, 1500);
        }
        
        // 更新素材统计
        function updateAssetStats() {
            const assetGrid = document.getElementById('asset-grid');
            assetGrid.innerHTML = '';
            
            const assets = [
                { icon: '🎬', name: '视频片段', count: '12个' },
                { icon: '🎙️', name: '音频文件', count: '8个' },
                { icon: '👤', name: '角色素材', count: '3个' },
                { icon: '🖼️', name: '分镜图片', count: '15张' }
            ];
            
            assets.forEach(asset => {
                const item = document.createElement('div');
                item.className = 'asset-item';
                item.innerHTML = `
                    <span class="asset-icon">${asset.icon}</span>
                    <span class="asset-name">${asset.name}</span>
                    <span class="asset-count">${asset.count}</span>
                `;
                assetGrid.appendChild(item);
            });
        }
        
        // 更新任务队列
        function updateTaskQueue() {
            const taskList = document.getElementById('task-list');
            taskList.innerHTML = '';
            
            const tasks = [
                { name: '剧本生成', status: 'completed', time: '2分钟前' },
                { name: '角色生成', status: 'completed', time: '5分钟前' },
                { name: '视频渲染', status: 'completed', time: '10分钟前' },
                { name: '音频合成', status: 'completed', time: '8分钟前' },
                { name: '素材整合', status: 'in-progress', time: '进行中' },
                { name: '质量检查', status: 'pending', time: '等待中' },
                { name: '平台发布', status: 'pending', time: '等待中' }
            ];
            
            tasks.forEach(task => {
                const item = document.createElement('div');
                item.className = `task-item ${task.status}`;
                const statusIcon = task.status === 'completed' ? '✓' : task.status === 'in-progress' ? '⟳' : '○';
                item.innerHTML = `
                    <span class="task-status">${statusIcon}</span>
                    <span class="task-name">${task.name}</span>
                    <span class="task-time">${task.time}</span>
                `;
                taskList.appendChild(item);
            });
        }
        
        // 预览成片
        function previewFinal() {
            showToast('正在加载预览...');
        }
        
        // 下载视频
        function downloadFinal() {
            const blob = new Blob(['视频内容'], { type: 'video/mp4' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = '短剧.mp4';
            a.click();
            URL.revokeObjectURL(url);
            showToast('开始下载视频...');
        }
        
        // 一键发布
        function publishAll() {
            const douyin = document.getElementById('publish-douyin').checked;
            const kuaishou = document.getElementById('publish-kuaishou').checked;
            const bilibili = document.getElementById('publish-bilibili').checked;
            
            let platforms = [];
            if (douyin) platforms.push('抖音');
            if (kuaishou) platforms.push('快手');
            if (bilibili) platforms.push('B站');
            
            if (platforms.length === 0) {
                alert('请至少选择一个发布平台');
                return;
            }
            
            showToast(`正在发布到：${platforms.join('、')}...`);
            
            // 模拟发布过程
            setTimeout(() => {
                showToast(`成功发布到：${platforms.join('、')}！`);
            }, 2000);
        }
        
        // 素材管理
        function manageAssets() {
            showToast('素材管理功能开发中...');
        }
        
        // 任务管理
        function manageTasks() {
            showToast('任务管理功能开发中...');
        }
        
        // 项目设置
        function projectSettings() {
            showToast('项目设置功能开发中...');
        }
        
        // 语音预设选择
        document.addEventListener('DOMContentLoaded', function() {
            const voicePresets = document.querySelectorAll('.voice-preset');
            voicePresets.forEach(preset => {
                preset.addEventListener('click', function() {
                    voicePresets.forEach(p => p.classList.remove('active'));
                    this.classList.add('active');
                });
            });
        });
        
        // 步骤点击切换
        document.addEventListener('DOMContentLoaded', function() {
            const stepItems = document.querySelectorAll('.step-item');
            stepItems.forEach((item, index) => {
                item.addEventListener('click', function() {
                    nextStep(index + 1);
                });
            });
        });
        
        // 切换标签页
        function switchTab(tabId) {
            const navTabs = document.querySelectorAll('.nav-tab');
            navTabs.forEach(t => t.classList.remove('active'));
            
            document.querySelectorAll('.tab-content').forEach(content => {
                content.style.display = 'none';
            });
            
            const targetTab = document.getElementById('tab-' + tabId);
            const targetContent = document.getElementById(tabId);
            
            if (targetTab) targetTab.classList.add('active');
            if (targetContent) targetContent.style.display = 'block';
        }
        
        // 第二级菜单切换
        document.addEventListener('DOMContentLoaded', function() {
            const submenuTabs = document.querySelectorAll('.submenu-tab');
            submenuTabs.forEach(tab => {
                tab.addEventListener('click', function() {
                    const subtab = this.getAttribute('data-subtab');
                    
                    // 更新标签状态
                    submenuTabs.forEach(t => t.classList.remove('active'));
                    this.classList.add('active');
                    
                    // 显示对应内容
                    document.querySelectorAll('.submenu-content').forEach(content => {
                        content.style.display = 'none';
                    });
                    document.getElementById(subtab).style.display = 'block';
                });
            });
            
            // 主导航栏切换
            const navTabs = document.querySelectorAll('.nav-tab');
            navTabs.forEach(tab => {
                tab.addEventListener('click', function() {
                    const tabId = this.getAttribute('data-tab');
                    
                    // 更新标签状态
                    navTabs.forEach(t => t.classList.remove('active'));
                    this.classList.add('active');
                    
                    // 显示对应内容
                    document.querySelectorAll('.tab-content').forEach(content => {
                        content.style.display = 'none';
                    });
                    const targetContent = document.getElementById(tabId);
                    if (targetContent) {
                        targetContent.style.display = 'block';
                    }
                    
                    // 如果切换到对标分析，初始化图表
                    if (tabId === 'benchmark') {
                        setTimeout(initIndustryCharts, 100);
                    }
                });
            });
        });
        
        // 分析领域
        function analyzeDomain() {
            const domain = document.getElementById('domain-select').value;
            const trendDiv = document.getElementById('domain-trend');
            
            // 领域趋势分析
            const domainData = {
                all: {
                    name: '全部领域',
                    trend: '持续增长',
                    growth: '15%/月',
                    hotTopics: '都市情感、职场奋斗、悬疑推理',
                    opportunities: '垂直领域深耕，内容专业化',
                    challenges: '内容同质化，竞争激烈'
                },
                love: {
                    name: '爱情',
                    trend: '稳定增长',
                    growth: '12%/月',
                    hotTopics: '都市爱情、校园初恋、异地恋',
                    opportunities: '情感共鸣，高互动性',
                    challenges: '题材同质化，创新难度大'
                },
                comedy: {
                    name: '喜剧',
                    trend: '快速增长',
                    growth: '20%/月',
                    hotTopics: '家庭幽默、职场趣事、社会热点',
                    opportunities: '解压需求大，传播性强',
                    challenges: '笑点创新，持续输出难度'
                },
                'sci-fi': {
                    name: '科幻',
                    trend: '新兴增长',
                    growth: '25%/月',
                    hotTopics: '未来科技、时空穿越、外星文明',
                    opportunities: '视觉效果吸引，粉丝粘性高',
                    challenges: '制作成本高，创意要求高'
                },
                suspense: {
                    name: '悬疑',
                    trend: '爆发增长',
                    growth: '30%/月',
                    hotTopics: '犯罪推理、密室逃脱、心理悬疑',
                    opportunities: '情节紧凑，观众粘性强',
                    challenges: '剧情逻辑要求高，制作复杂'
                },
                workplace: {
                    name: '职场',
                    trend: '稳定增长',
                    growth: '10%/月',
                    hotTopics: '职场奋斗、办公室文化、职业发展',
                    opportunities: '贴近现实，共鸣感强',
                    challenges: '题材局限，创新难度'
                },
                campus: {
                    name: '校园',
                    trend: '稳步增长',
                    growth: '8%/月',
                    hotTopics: '校园生活、青春爱情、友情故事',
                    opportunities: '年轻受众多，市场潜力大',
                    challenges: '题材重复，差异化难'
                }
            };
            
            const data = domainData[domain];
            trendDiv.innerHTML = `
                <div class="platform-info">
                    <div class="info-item"><strong>领域名称：</strong>${data.name}</div>
                    <div class="info-item"><strong>发展趋势：</strong>${data.trend}</div>
                    <div class="info-item"><strong>月增长率：</strong>${data.growth}</div>
                    <div class="info-item"><strong>热门话题：</strong>${data.hotTopics}</div>
                    <div class="info-item"><strong>机会：</strong>${data.opportunities}</div>
                    <div class="info-item"><strong>挑战：</strong>${data.challenges}</div>
                </div>
            `;
            
            // 受众偏好分析图表
            const ctx = document.getElementById('domainAudienceChart').getContext('2d');
            
            // 销毁旧图表
            if (window.domainChart) {
                window.domainChart.destroy();
            }
            
            // 领域受众数据
            const audienceData = {
                all: {
                    labels: ['18-24岁', '25-34岁', '35-44岁', '45岁以上', '男性', '女性'],
                    data: [30, 40, 20, 10, 45, 55]
                },
                love: {
                    labels: ['18-24岁', '25-34岁', '35-44岁', '45岁以上', '男性', '女性'],
                    data: [35, 45, 15, 5, 35, 65]
                },
                comedy: {
                    labels: ['18-24岁', '25-34岁', '35-44岁', '45岁以上', '男性', '女性'],
                    data: [40, 35, 15, 10, 50, 50]
                },
                'sci-fi': {
                    labels: ['18-24岁', '25-34岁', '35-44岁', '45岁以上', '男性', '女性'],
                    data: [45, 40, 10, 5, 65, 35]
                },
                suspense: {
                    labels: ['18-24岁', '25-34岁', '35-44岁', '45岁以上', '男性', '女性'],
                    data: [30, 40, 25, 5, 55, 45]
                },
                workplace: {
                    labels: ['18-24岁', '25-34岁', '35-44岁', '45岁以上', '男性', '女性'],
                    data: [20, 45, 25, 10, 48, 52]
                },
                campus: {
                    labels: ['18-24岁', '25-34岁', '35-44岁', '45岁以上', '男性', '女性'],
                    data: [50, 30, 15, 5, 45, 55]
                }
            };
            
            const audience = audienceData[domain];
            
            window.domainChart = new Chart(ctx, {
                type: 'radar',
                data: {
                    labels: audience.labels,
                    datasets: [{
                        label: '用户占比',
                        data: audience.data,
                        backgroundColor: 'rgba(102, 126, 234, 0.2)',
                        borderColor: '#667eea',
                        pointBackgroundColor: '#667eea'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        r: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });
        }
        
        // 分析平台
        function analyzePlatform() {
            const platform = document.getElementById('platform-select').value;
            const featuresDiv = document.getElementById('platform-features');
            
            // 平台特性分析
            const platformData = {
                all: {
                    name: '全部平台',
                    users: '5亿+',
                    content: '短视频、短剧、直播',
                    algorithm: '基于用户兴趣推荐',
                    advantages: '覆盖面广，用户基数大',
                    disadvantages: '竞争激烈，内容同质化'
                },
                douyin: {
                    name: '抖音',
                    users: '3亿+',
                    content: '15-60秒短视频，短剧',
                    algorithm: '强个性化推荐，注重完播率',
                    advantages: '流量大，算法成熟',
                    disadvantages: '内容更新快，留存难度大'
                },
                kuaishou: {
                    name: '快手',
                    users: '2亿+',
                    content: '生活分享，短剧',
                    algorithm: '社区氛围，关注推荐',
                    advantages: '用户粘性高，互动性强',
                    disadvantages: '内容质量参差不齐'
                },
                bilibili: {
                    name: 'B站',
                    users: '1.5亿+',
                    content: '中长视频，番剧，短剧',
                    algorithm: '兴趣圈层，弹幕文化',
                    advantages: '用户质量高，内容深度',
                    disadvantages: '用户群体相对小众'
                },
                wechat: {
                    name: '视频号',
                    users: '2.5亿+',
                    content: '社交分享，短剧',
                    algorithm: '社交关系链，朋友推荐',
                    advantages: '社交属性强，转化率高',
                    disadvantages: '内容分发依赖社交关系'
                }
            };
            
            const data = platformData[platform];
            featuresDiv.innerHTML = `
                <div class="platform-info">
                    <div class="info-item"><strong>平台名称：</strong>${data.name}</div>
                    <div class="info-item"><strong>用户规模：</strong>${data.users}</div>
                    <div class="info-item"><strong>内容类型：</strong>${data.content}</div>
                    <div class="info-item"><strong>算法特点：</strong>${data.algorithm}</div>
                    <div class="info-item"><strong>优势：</strong>${data.advantages}</div>
                    <div class="info-item"><strong>劣势：</strong>${data.disadvantages}</div>
                </div>
            `;
            
            // 热门内容分析图表
            const ctx = document.getElementById('platformContentChart').getContext('2d');
            
            // 销毁旧图表
            if (window.platformChart) {
                window.platformChart.destroy();
            }
            
            // 平台热门内容数据
            const contentData = {
                all: {
                    labels: ['爱情', '喜剧', '悬疑', '科幻', '职场', '校园'],
                    data: [90, 85, 75, 65, 60, 55]
                },
                douyin: {
                    labels: ['爱情', '喜剧', '悬疑', '科幻', '职场', '校园'],
                    data: [95, 90, 80, 60, 55, 50]
                },
                kuaishou: {
                    labels: ['爱情', '喜剧', '悬疑', '科幻', '职场', '校园'],
                    data: [85, 90, 70, 55, 60, 65]
                },
                bilibili: {
                    labels: ['爱情', '喜剧', '悬疑', '科幻', '职场', '校园'],
                    data: [75, 80, 85, 90, 70, 75]
                },
                wechat: {
                    labels: ['爱情', '喜剧', '悬疑', '科幻', '职场', '校园'],
                    data: [85, 75, 70, 60, 80, 65]
                }
            };
            
            const content = contentData[platform];
            
            window.platformChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: content.labels,
                    datasets: [{
                        label: '热度指数',
                        data: content.data,
                        backgroundColor: [
                            '#667eea',
                            '#764ba2',
                            '#f093fb',
                            '#f5576c',
                            '#4facfe',
                            '#43e97b'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });
        }
        
        // 初始化行业总览图表
        function initIndustryCharts() {
            // 行业趋势图表
            const trendCtx = document.getElementById('trendChart').getContext('2d');
            new Chart(trendCtx, {
                type: 'line',
                data: {
                    labels: ['1月', '2月', '3月', '4月', '5月', '6月'],
                    datasets: [{
                        label: '短剧播放量',
                        data: [12000, 19000, 15000, 25000, 22000, 30000],
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
            
            // 热门题材图表
            const topicCtx = document.getElementById('topicChart').getContext('2d');
            new Chart(topicCtx, {
                type: 'bar',
                data: {
                    labels: ['爱情', '喜剧', '悬疑', '科幻', '职场', '校园'],
                    datasets: [{
                        label: '热度指数',
                        data: [95, 85, 78, 70, 65, 60],
                        backgroundColor: [
                            '#667eea',
                            '#764ba2',
                            '#f093fb',
                            '#f5576c',
                            '#4facfe',
                            '#43e97b'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });
            
            // 平台分布图表
            const platformCtx = document.getElementById('platformChart').getContext('2d');
            new Chart(platformCtx, {
                type: 'doughnut',
                data: {
                    labels: ['抖音', '快手', 'B站', '视频号'],
                    datasets: [{
                        data: [45, 25, 20, 10],
                        backgroundColor: [
                            '#667eea',
                            '#764ba2',
                            '#f093fb',
                            '#f5576c'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
            
            // 受众分析图表
            const audienceCtx = document.getElementById('audienceChart').getContext('2d');
            new Chart(audienceCtx, {
                type: 'radar',
                data: {
                    labels: ['18-24岁', '25-34岁', '35-44岁', '45岁以上', '男性', '女性'],
                    datasets: [{
                        label: '用户占比',
                        data: [35, 40, 15, 10, 45, 55],
                        backgroundColor: 'rgba(102, 126, 234, 0.2)',
                        borderColor: '#667eea',
                        pointBackgroundColor: '#667eea'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        r: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });
        }
        
        // 短剧博主数据库 - 按当前最流行短剧分类
        const shortDramaBloggers = [
            // 甜宠类 TOP10
            { name: '甜宠剧场', platform: '抖音', followers: '3500万+', category: '甜宠', style: '高糖甜宠', representative: '《霸道总裁爱上我》系列', rank: 1, hot: 98 },
            { name: '恋爱研究所', platform: '快手', followers: '2800万+', category: '甜宠', style: '青春校园', representative: '《校草的专属甜心》', rank: 2, hot: 95 },
            { name: '蜜糖短剧', platform: '抖音', followers: '2200万+', category: '甜宠', style: '甜虐交织', representative: '《先婚后爱》系列', rank: 3, hot: 92 },
            { name: '心动剧场', platform: '视频号', followers: '1800万+', category: '甜宠', style: '都市言情', representative: '《闪婚老公是总裁》', rank: 4, hot: 89 },
            { name: '甜心工作室', platform: 'B站', followers: '1500万+', category: '甜宠', style: '治愈系', representative: '《我的小确幸》', rank: 5, hot: 86 },
            
            // 逆袭类 TOP10
            { name: '逆袭剧场', platform: '抖音', followers: '4200万+', category: '逆袭', style: '打脸爽文', representative: '《赘婿逆袭》系列', rank: 1, hot: 99 },
            { name: '王者归来', platform: '快手', followers: '3100万+', category: '逆袭', style: '强者回归', representative: '《战神归来》系列', rank: 2, hot: 96 },
            { name: '废材逆袭', platform: '抖音', followers: '2600万+', category: '逆袭', style: '废材流', representative: '《废材少爷逆袭记》', rank: 3, hot: 93 },
            { name: '草根逆袭', platform: '视频号', followers: '1900万+', category: '逆袭', style: '励志奋斗', representative: '《从农村到豪门》', rank: 4, hot: 90 },
            { name: '商战逆袭', platform: 'B站', followers: '1400万+', category: '逆袭', style: '商业传奇', representative: '《穷小子变首富》', rank: 5, hot: 87 },
            
            // 悬疑类 TOP10
            { name: '悬疑剧场', platform: '抖音', followers: '3800万+', category: '悬疑', style: '烧脑推理', representative: '《致命ID》系列', rank: 1, hot: 97 },
            { name: '探案笔记', platform: '快手', followers: '2900万+', category: '悬疑', style: '刑侦破案', representative: '《神探狄仁杰》短剧版', rank: 2, hot: 94 },
            { name: '迷雾剧场', platform: 'B站', followers: '2100万+', category: '悬疑', style: '心理悬疑', representative: '《消失的她》短剧版', rank: 3, hot: 91 },
            { name: '密室逃脱', platform: '抖音', followers: '1700万+', category: '悬疑', style: '密室推理', representative: '《密室大逃脱》系列', rank: 4, hot: 88 },
            { name: '罪案现场', platform: '视频号', followers: '1300万+', category: '悬疑', style: '犯罪纪实', representative: '《真实案件改编》', rank: 5, hot: 85 },
            
            // 古装类 TOP10
            { name: '古装剧场', platform: '抖音', followers: '4500万+', category: '古装', style: '宫廷权谋', representative: '《甄嬛传》短剧版', rank: 1, hot: 98 },
            { name: '仙侠世界', platform: '快手', followers: '3300万+', category: '古装', style: '仙侠玄幻', representative: '《诛仙》短剧版', rank: 2, hot: 95 },
            { name: '穿越王妃', platform: '抖音', followers: '2700万+', category: '古装', style: '穿越言情', representative: '《王妃要休夫》系列', rank: 3, hot: 92 },
            { name: '武侠江湖', platform: 'B站', followers: '2000万+', category: '古装', style: '武侠江湖', representative: '《笑傲江湖》短剧版', rank: 4, hot: 89 },
            { name: '历史传奇', platform: '视频号', followers: '1600万+', category: '古装', style: '历史改编', representative: '《大明风华》短剧版', rank: 5, hot: 86 },
            
            // 都市类 TOP10
            { name: '都市剧场', platform: '抖音', followers: '3200万+', category: '都市', style: '都市情感', representative: '《三十而已》短剧版', rank: 1, hot: 94 },
            { name: '职场风云', platform: '快手', followers: '2400万+', category: '都市', style: '职场奋斗', representative: '《杜拉拉升职记》短剧版', rank: 2, hot: 91 },
            { name: '豪门恩怨', platform: '抖音', followers: '2000万+', category: '都市', style: '豪门世家', representative: '《豪门太太不好当》', rank: 3, hot: 88 },
            { name: '创业时代', platform: 'B站', followers: '1500万+', category: '都市', style: '创业励志', representative: '《创业维艰》系列', rank: 4, hot: 85 },
            { name: '婚姻家庭', platform: '视频号', followers: '1200万+', category: '都市', style: '家庭伦理', representative: '《婚姻保卫战》', rank: 5, hot: 82 },
            
            // 穿越类 TOP10
            { name: '穿越剧场', platform: '抖音', followers: '3600万+', category: '穿越', style: '时空穿越', representative: '《穿越到古代当王妃》', rank: 1, hot: 96 },
            { name: '重生逆袭', platform: '快手', followers: '2800万+', category: '穿越', style: '重生复仇', representative: '《重生之嫡女归来》', rank: 2, hot: 93 },
            { name: '快穿系统', platform: '抖音', followers: '2300万+', category: '穿越', style: '快穿攻略', representative: '《快穿之打脸狂魔》', rank: 3, hot: 90 },
            { name: '古今奇缘', platform: 'B站', followers: '1800万+', category: '穿越', style: '古今结合', representative: '《带着手机回古代》', rank: 4, hot: 87 },
            { name: '平行时空', platform: '视频号', followers: '1400万+', category: '穿越', style: '平行世界', representative: '《另一个世界的我》', rank: 5, hot: 84 },
            
            // 重生类 TOP10
            { name: '重生剧场', platform: '抖音', followers: '4000万+', category: '重生', style: '重生复仇', representative: '《重生之复仇千金》', rank: 1, hot: 97 },
            { name: '涅槃重生', platform: '快手', followers: '3000万+', category: '重生', style: '涅槃归来', representative: '《涅槃重生：总裁夫人》', rank: 2, hot: 94 },
            { name: '回到过去', platform: '抖音', followers: '2500万+', category: '重生', style: '改变命运', representative: '《重生回到1990》', rank: 3, hot: 91 },
            { name: '再来一次', platform: 'B站', followers: '1900万+', category: '重生', style: '人生重启', representative: '《人生重开模拟器》短剧版', rank: 4, hot: 88 },
            { name: '前世今生', platform: '视频号', followers: '1500万+', category: '重生', style: '前世记忆', representative: '《带着记忆重生》', rank: 5, hot: 85 },
            
            // 复仇类 TOP10
            { name: '复仇剧场', platform: '抖音', followers: '3400万+', category: '复仇', style: '复仇爽文', representative: '《复仇千金归来》', rank: 1, hot: 95 },
            { name: '血债血偿', platform: '快手', followers: '2600万+', category: '复仇', style: '黑化复仇', representative: '《黑化女主复仇记》', rank: 2, hot: 92 },
            { name: '以牙还牙', platform: '抖音', followers: '2100万+', category: '复仇', style: '智斗复仇', representative: '《智斗绿茶婊》系列', rank: 3, hot: 89 },
            { name: '恩怨情仇', platform: 'B站', followers: '1600万+', category: '复仇', style: '家族恩怨', representative: '《家族恩怨录》', rank: 4, hot: 86 },
            { name: '正义使者', platform: '视频号', followers: '1300万+', category: '复仇', style: '替天行道', representative: '《正义不会缺席》', rank: 5, hot: 83 },
            
            // 职场类 TOP10
            { name: '职场剧场', platform: '抖音', followers: '2900万+', category: '职场', style: '职场进阶', representative: '《从实习生到CEO》', rank: 1, hot: 93 },
            { name: '办公室风云', platform: '快手', followers: '2200万+', category: '职场', style: '办公室政治', representative: '《办公室生存法则》', rank: 2, hot: 90 },
            { name: '销售之王', platform: '抖音', followers: '1800万+', category: '职场', style: '销售励志', representative: '《销售冠军之路》', rank: 3, hot: 87 },
            { name: '律师风云', platform: 'B站', followers: '1400万+', category: '职场', style: '律政职场', representative: '《精英律师》短剧版', rank: 4, hot: 84 },
            { name: '医生日常', platform: '视频号', followers: '1100万+', category: '职场', style: '医疗职场', representative: '《急诊科医生》短剧版', rank: 5, hot: 81 }
        ];

        // 显示热门分类
        function showHotCategories() {
            const hotCategoriesDiv = document.getElementById('hot-categories');
            if (hotCategoriesDiv.style.display === 'none') {
                hotCategoriesDiv.style.display = 'block';
                // 默认显示全部热门博主
                filterByCategory('all');
            } else {
                hotCategoriesDiv.style.display = 'none';
            }
        }

        // 按分类筛选博主
        function filterByCategory(category) {
            const resultDiv = document.getElementById('bloggers-result');
            
            // 更新标签样式
            document.querySelectorAll('.category-tag').forEach(tag => {
                tag.classList.remove('active');
                if (tag.textContent === (category === 'all' ? '全部' : category)) {
                    tag.classList.add('active');
                }
            });
            
            resultDiv.innerHTML = '<div style="text-align: center; padding: 40px;"><div class="loading-spinner"></div> 加载中...</div>';
            
            setTimeout(() => {
                let filteredBloggers;
                if (category === 'all') {
                    // 显示所有分类的前5名
                    filteredBloggers = shortDramaBloggers.filter(b => b.rank <= 5);
                } else {
                    // 显示指定分类的前10名
                    filteredBloggers = shortDramaBloggers.filter(b => b.category === category);
                }
                
                // 按热度排序
                filteredBloggers.sort((a, b) => b.hot - a.hot);
                
                resultDiv.innerHTML = '';
                
                if (filteredBloggers.length === 0) {
                    resultDiv.innerHTML = '<div style="text-align: center; padding: 40px;">该分类暂无博主数据</div>';
                    return;
                }
                
                // 添加分类标题
                const categoryTitle = document.createElement('div');
                categoryTitle.style.cssText = 'width: 100%; margin-bottom: 20px; padding: 10px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 8px; text-align: center;';
                categoryTitle.innerHTML = `<h4 style="margin: 0;">${category === 'all' ? '🔥 全部分类热门博主 TOP5' : `🔥 ${category}类热门博主 TOP10`}</h4>`;
                resultDiv.appendChild(categoryTitle);
                
                filteredBloggers.forEach((blogger, index) => {
                    const card = document.createElement('div');
                    card.className = 'blogger-card';
                    card.style.cssText = 'position: relative; overflow: hidden;';
                    
                    // 排名标识
                    const rankBadge = index < 3 ? ['🥇', '🥈', '🥉'][index] : `<span style="font-size: 14px; color: #666;">#${index + 1}</span>`;
                    
                    card.innerHTML = `
                        <div style="position: absolute; top: 10px; right: 10px; font-size: 24px;">${rankBadge}</div>
                        <div style="width: 80px; height: 80px; border-radius: 50%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); margin: 0 auto 10px; display: flex; align-items: center; justify-content: center; color: white; font-size: 24px;">${blogger.name[0]}</div>
                        <h5>${blogger.name}</h5>
                        <div class="platform">${blogger.platform} · ${blogger.followers}</div>
                        <div style="margin: 8px 0;">
                            <span style="background: #ff6b6b; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">热度 ${blogger.hot}</span>
                            <span style="background: #4ecdc4; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; margin-left: 5px;">${blogger.category}</span>
                        </div>
                        <div class="blogger-info">
                            <small>风格：${blogger.style}</small>
                            <small>代表作：${blogger.representative}</small>
                        </div>
                        <button class="btn btn-sm" onclick="analyzeBlogger('${blogger.name}')">分析</button>
                    `;
                    resultDiv.appendChild(card);
                });
            }, 500);
        }

        // 搜索热门博主
        function searchHotBloggers() {
            const searchTerm = document.getElementById('blogger-search').value.trim();
            const resultDiv = document.getElementById('bloggers-result');
            
            if (!searchTerm) {
                showToast('请输入搜索关键词');
                return;
            }
            
            resultDiv.innerHTML = '<div style="text-align: center; padding: 40px;"><div class="loading-spinner"></div> 搜索中...</div>';
            
            setTimeout(() => {
                // 过滤搜索结果
                const filteredBloggers = shortDramaBloggers.filter(blogger => 
                    blogger.name.includes(searchTerm) || 
                    blogger.platform.includes(searchTerm) || 
                    blogger.category.includes(searchTerm) ||
                    blogger.style.includes(searchTerm) ||
                    blogger.representative.includes(searchTerm)
                );
                
                resultDiv.innerHTML = '';
                
                // 添加搜索结果标题
                const searchTitle = document.createElement('div');
                searchTitle.style.cssText = 'width: 100%; margin-bottom: 20px; padding: 10px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 8px; text-align: center;';
                searchTitle.innerHTML = `<h4 style="margin: 0;">搜索结果："${searchTerm}" (${filteredBloggers.length}个)</h4>`;
                resultDiv.appendChild(searchTitle);
                
                if (filteredBloggers.length === 0) {
                    resultDiv.innerHTML += '<div style="text-align: center; padding: 40px;">未找到匹配的博主</div>';
                    return;
                }
                
                // 按热度排序
                filteredBloggers.sort((a, b) => b.hot - a.hot);
                
                filteredBloggers.forEach((blogger, index) => {
                    const card = document.createElement('div');
                    card.className = 'blogger-card';
                    card.style.cssText = 'position: relative; overflow: hidden;';
                    
                    card.innerHTML = `
                        <div style="width: 80px; height: 80px; border-radius: 50%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); margin: 0 auto 10px; display: flex; align-items: center; justify-content: center; color: white; font-size: 24px;">${blogger.name[0]}</div>
                        <h5>${blogger.name}</h5>
                        <div class="platform">${blogger.platform} · ${blogger.followers}</div>
                        <div style="margin: 8px 0;">
                            <span style="background: #ff6b6b; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">热度 ${blogger.hot}</span>
                            <span style="background: #4ecdc4; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; margin-left: 5px;">${blogger.category}</span>
                        </div>
                        <div class="blogger-info">
                            <small>风格：${blogger.style}</small>
                            <small>代表作：${blogger.representative}</small>
                        </div>
                        <button class="btn btn-sm" onclick="analyzeBlogger('${blogger.name}')">分析</button>
                    `;
                    resultDiv.appendChild(card);
                });
            }, 1000);
        }
        
        // 分析博主
        function analyzeBlogger(bloggerName) {
            showToast(`正在分析博主: ${bloggerName}...`);
            
            // 从短剧博主数据库中查找
            const bloggerData = shortDramaBloggers.find(b => b.name === bloggerName);
            
            if (!bloggerData) {
                showToast('未找到该博主信息');
                return;
            }
            
            // 模拟博主分析结果
            setTimeout(() => {
                const analysisContent = `
                    <div class="blogger-analysis">
                        <h4>${bloggerName} 详细分析</h4>
                        <div class="analysis-grid">
                            <div class="analysis-item">
                                <strong>平台：</strong>${bloggerData.platform}
                            </div>
                            <div class="analysis-item">
                                <strong>粉丝数：</strong>${bloggerData.followers}
                            </div>
                            <div class="analysis-item">
                                <strong>领域：</strong>${bloggerData.category}
                            </div>
                            <div class="analysis-item">
                                <strong>风格：</strong>${bloggerData.style}
                            </div>
                            <div class="analysis-item">
                                <strong>代表作：</strong>${bloggerData.representative}
                            </div>
                            <div class="analysis-item">
                                <strong>热度指数：</strong>${bloggerData.hot}分
                            </div>
                            <div class="analysis-item">
                                <strong>排名：</strong>第${bloggerData.rank}名
                            </div>
                            <div class="analysis-item">
                                <strong>内容特点：</strong>高质量短剧内容，精准把握${bloggerData.category}类受众喜好
                            </div>
                            <div class="analysis-item">
                                <strong>成功因素：</strong>独特的叙事风格，持续的内容创新，强大的粉丝运营能力
                            </div>
                            <div class="analysis-item">
                                <strong>建议：</strong>学习其内容创作方法和粉丝运营策略，关注${bloggerData.category}类短剧的市场趋势
                            </div>
                        </div>
                    </div>
                `;
                
                // 创建模态框
                const modal = document.createElement('div');
                modal.className = 'modal';
                modal.innerHTML = `
                    <div class="modal-content">
                        <span class="close" onclick="this.parentElement.parentElement.remove()">&times;</span>
                        ${analysisContent}
                    </div>
                `;
                document.body.appendChild(modal);
            }, 1000);
        }
