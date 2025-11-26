多人协同开发过程中需要创建新的本地分支以避免和其他人产生冲突，记录一下操作内容：

### 创建并切换到新的本地分支
```
# 在主分支确保主分支更新
git checkout main
git pull origin main

# 创建并切换到新分支
git checkout -b exBranch
```

### 推送远程分支
```
# 第一次推送需要指定远程分支
git push -u origin exBranch
```

### 同步更新与避免冲突
开发过程中分支应该以工作模块为单位创建以便管理回溯。

至于开发过程中常见的冲突问题，可以通过定期更新主分支与合并进行处理：
```
# 切换到主分支并更新 
git checkout main git pull origin main 

# 切回你的特性分支 
git checkout exBranch 

# 合并主分支的最新更改 
git merge main
```

### 开发完成后的合并
- 首先要确保分支已经推送到远程
```
git push origin exBranch
```
- 在远程仓库中创建一个从`exBranch` -> `master` 的 `Pull Request`
- 代码审查等通过后合并

#### 合并时解决冲突
如果a分支推送到远程并发出pull request，在a审查的过程中b分支也推送到远程发送pull request，且a和b分支存在冲突。此时b是不能直接合并到master分支的，应该由审查打回后，由b重新修改后推送：
```
# 1. 切换到 b 分支 
git checkout b

# 2. 拉取最新 master 
git fetch origin 
git rebase origin/master 

# 3. 手动解决冲突（如果有） 
# - 编辑冲突文件 
# - git add <resolved-file> 
# - git rebase --continue 

# 4. 强制推送到远程 bb 分支（因为 rebase 改写了历史） 
git push --force-with-lease origin b
```
