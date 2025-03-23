export PATH=$PATH:/usr/local/mysql/bin

eval "$(/opt/homebrew/bin/brew shellenv)"
export FLASK_APP=naledi.main
export GOOGLE_CLOUD_PROJECT="spazachain"
export PATH="/opt/homebrew/opt/postgresql@14/bin:$PATH"
export LDFLAGS="-L/opt/homebrew/opt/postgresql@14/lib"
export CPPFLAGS="-I/opt/homebrew/opt/postgresql@14/include"
export PKG_CONFIG_PATH="/opt/homebrew/opt/postgresql@14/lib/pkgconfig"
export PATH="/opt/homebrew/bin:$PATH"
export LDFLAGS="-L/opt/homebrew/opt/openssl@3/lib"
export CPPFLAGS="-I/opt/homebrew/opt/openssl@3/include"
export PKG_CONFIG_PATH="/opt/homebrew/opt/openssl@3/lib/pkgconfig"
# The following lines have been added by Docker Desktop to enable Docker CLI completions.
fpath=(/Users/jackykotane/.docker/completions $fpath)
autoload -Uz compinit
compinit
# End of Docker CLI completions
export PATH="/opt/homebrew/opt/openldap/bin:$PATH"
export PATH="/opt/homebrew/opt/openldap/sbin:$PATH"
export PATH="/opt/homebrew/opt/openldap/bin:$PATH"
export PATH="/opt/homebrew/opt/openldap/sbin:$PATH"
export PATH="/opt/homebrew/opt/openldap/sbin:$PATH"
export PATH="/opt/homebrew/opt/openldap/bin:$PATH"

# Added by Windsurf
export PATH="/Users/jackykotane/.codeium/windsurf/bin:$PATH"
