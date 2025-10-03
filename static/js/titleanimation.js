const h1 = document.querySelector('h1')
h1.innerHTML = h1.textContent.replace(/\S/g, "<span>$&</span>")

document.querySelectorAll('span').forEach((span, index) => {
  span.style.setProperty('--delay', `${index * 0.1}s`)
})

// 页面加载时自动触发动画
window.addEventListener('DOMContentLoaded', () => {
  // 设置默认动画类型
  h1.style.setProperty('--animation', 'jump')
  
  // 添加动画类
  h1.classList.add('animate')
  
  // 每隔2秒切换一种动画效果
  const animations = ['jump', 'pop', 'flip'];
  let currentIndex = 0;
  
  setInterval(() => {
    currentIndex = (currentIndex + 1) % animations.length;
    h1.style.setProperty('--animation', animations[currentIndex]);
    
    h1.classList.remove('animate')
    void h1.offsetWidth
    h1.classList.add('animate')
  }, 2000);
})