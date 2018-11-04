if grep --quiet "alias brownie=" ~/.bash_aliases; then
    echo "Brownie is already installed."
else
    echo "alias brownie=\"${PWD}\"" >> ~/.bash_aliases
    echo "Brownie has been installed!"
fi