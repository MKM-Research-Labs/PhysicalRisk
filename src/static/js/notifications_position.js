
        function getPositionStyles(pos) {
            const positions = {
                'top-right': 'top:20px;right:20px;',
                'top-left': 'top:20px;left:20px;',
                'top-center': 'top:20px;left:50%;transform:translateX(-50%);',
                'bottom-right': 'bottom:20px;right:20px;',
                'bottom-left': 'bottom:20px;left:20px;',
                'bottom-center': 'bottom:20px;left:50%;transform:translateX(-50%);'
            };
            return positions[pos] || positions['top-right'];
        }
        