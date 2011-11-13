if &cp | set nocp | endif
let s:cpo_save=&cpo
set cpo&vim
inoremap <Nul> 
nnoremap  :call MaximizeToggle ()
nnoremap o :call MaximizeToggle ()
nnoremap O :call MaximizeToggle ()
noremap ae :clist
noremap fe :cfirst
nmap gx <Plug>NetrwBrowseX
noremap gc gdbvf
noremap gf vf
noremap ne :cn
noremap pe :cp
noremap tl :TlistToggle
noremap tw 
nnoremap <silent> <Plug>NetrwBrowseX :call netrw#NetrwBrowseX(expand("<cWORD>"),0)
map <F2> :NERDTreeTabsToggle
let &cpo=s:cpo_save
unlet s:cpo_save
set backspace=indent,eol,start
set copyindent
set expandtab
set fileencodings=ucs-bom,utf-8,default,latin1
set helplang=en
set history=1000
set hlsearch
set ignorecase
set incsearch
set nomodeline
set path=.,/usr/include,,,.,,/usr/lib/jvm/java-6-openjdk/src/**,
set printoptions=paper:letter
set ruler
set runtimepath=~/.vim,/var/lib/vim/addons,/usr/share/vim/vimfiles,/usr/share/vim/vim73,/usr/share/vim/vimfiles/after,/var/lib/vim/addons/after,~/.vim/after
set shiftround
set shiftwidth=4
set showmatch
set smartcase
set suffixes=.bak,~,.swp,.o,.info,.aux,.log,.dvi,.bbl,.blg,.brf,.cb,.ind,.idx,.ilg,.inx,.out,.toc
set noswapfile
set tabstop=4
set tags=./tags,./TAGS,tags,TAGS,~/.vimtags
set title
" vim: set ft=vim :
