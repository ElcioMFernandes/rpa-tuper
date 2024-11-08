import React from "react";

// Define as props para o ListItem
interface ListItemProps {
  children: React.ReactNode;
}

const ListItem: React.FC<ListItemProps> = ({ children }) => {
  return (
    <li className="py-4 px-4 border-b last:border-none flex items-center space-x-4">
      {children}
    </li>
  );
};

export default ListItem;
