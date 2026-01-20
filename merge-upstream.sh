
# Add upstream remote if not already added
git remote -v | grep "upstream" || git remote add upstream  https://github.com/eth-brownie/brownie.git
git fetch upstream
git merge upstream/master

echo "You probably have a lot of merge conflicts to fix. Get to work."